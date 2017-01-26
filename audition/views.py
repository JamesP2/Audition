from audition import app, facebook, login_manager
from audition.email import send_mail
from audition.models import *
from datetime import datetime
from flask import abort, g, render_template, render_template_string, request, session, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from flask_mail import Message
from flask_oauthlib.client import OAuthException
import glob
from markupsafe import Markup
import os.path


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    remember_me = True if 'remember_me' in request.form else False

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password(password):
        app.logger.warn('Incorrect login for %s', user)
        flash('Username or Password incorrect', 'danger')
        return redirect(url_for('login'))

    app.logger.info('%s Logging in', user)
    login_user(user, remember=remember_me)

    if 'WARN_EMAIL' in app.config and app.config['WARN_EMAIL'] and not validate_email(user.email):
        app.logger.info('%s has no valid email. They will be warned until it is changed.', user)

    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    app.logger.info('%s Logging out', current_user)
    logout_user()
    return redirect(url_for('index'))


@app.route('/facebookLogin')
def facebook_login():
    if not bool(app.config['SITE_ENABLED']):
        flash('Audition Booking is currently unavailable.', 'warning')
        return redirect(url_for('index'))

    callback_url = url_for('facebook_authorized',
                           next=request.args.get('next') or request.referrer or None,
                           _external=True)

    return facebook.authorize(callback=callback_url)


@app.route('/facebookAuthorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    app.logger.debug('Response from facebook: %s', resp)

    if resp is None:
        app.logger.warn('Access denied for facebook login. reason=%s error=%s' %
                        (request.args['error_reason'],
                         request.args['error_description']))

        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )

    if isinstance(resp, OAuthException):
        app.logger.error(OAuthException)
        return 'Access denied: %s' % resp.message

    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me', data={
        'fields': 'first_name,last_name,id,email'
    })

    provider = UserProvider.query.filter_by(user_uid=me.data['id'], provider_id='facebook').first()

    if provider is not None and provider.user is not None:
        app.logger.info('%s Logging in via Facebook', provider.user)
        login_user(provider.user)

    else:
        first_name = me.data['first_name'].replace(' ', '_')
        last_name = me.data['last_name'].replace(' ', '_')

        new_username = (first_name + '_' + last_name).lower()
        count = 1

        while User.query.filter_by(username=new_username).first() is not None:
            new_username = (first_name + '_' + last_name + str(count)).lower()
            count += 1

        new_user = User(first_name=first_name, last_name=last_name, username=new_username,
                        email=me.data['email'] if 'email' in me.data.keys() else '')
        new_user.providers.append(UserProvider(user_uid=me.data['id'], provider_id='facebook',
                                               email=me.data['email'] if 'email' in me.data.keys() else ''))

        db.session.add(new_user)
        db.session.commit()

        app.logger.info('%s Logging in via Facebook (new user)', new_user)
        login_user(new_user)

    if 'WARN_EMAIL' in app.config and app.config['WARN_EMAIL'] and not validate_email(current_user.email):
        app.logger.info('%s has no valid email. They will be warned until it is changed.', current_user)

    return redirect(request.args.get('next') or url_for('index'))


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.before_request
def before_request():
    g.user = current_user

    if 'WARN_EMAIL' in app.config and app.config['WARN_EMAIL'] \
            and current_user.is_authenticated and request.endpoint not in ['edit_profile', 'logout']:
        g.warn_email = not validate_email(current_user.email)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')

    return render_template('landing_page.html', site_enabled=bool(app.config['SITE_ENABLED']))


@app.route('/me')
@login_required
def my_auditions():
    return render_template('my_auditions.html',
                           user=current_user)


@app.route('/shows')
@login_required
def shows():
    return render_template('shows.html',
                           shows=Show.query.all())


@app.route('/show/<int:show_id>')
@login_required
def show(show_id):
    given_show = Show.query.get(show_id)

    if given_show is None:
        flash('Invalid show ID', 'danger')
        return redirect(url_for('index'))

    return render_template('show.html',
                           show=given_show)


@app.route('/show/<int:show_id>/manage')
@login_required
def manage_show(show_id):
    given_show = Show.query.get(show_id)

    if given_show is None:
        flash('Invalid show ID', 'danger')
        return redirect(url_for('index'))

    if given_show not in current_user.managed_shows:
        flash('You do not have permission to manage this show.', 'danger')
        return redirect(url_for('index'))

    return render_template('manage_show.html',
                           show=given_show)


@app.route('/show/<int:show_id>/manage/description', methods=['GET', 'POST'])
@login_required
def manage_show_description(show_id):
    given_show = Show.query.get(show_id)

    if request.method == 'POST':
        given_show.description = request.form['description']

        db.session.add(given_show)
        db.session.commit()

        app.logger.info('%s description changed by %s', given_show, current_user)

        return redirect(url_for('manage_show', show_id=show_id))

    return render_template('manage_show_description.html', show=given_show)


@app.route('/show/<int:show_id>/<string:date>/manage/description', methods=['GET', 'POST'])
@login_required
def manage_day_description(show_id, date):
    given_day = AuditionDay.query.get((date, show_id))

    if request.method == 'POST':
        given_day.description = request.form['description']

        db.session.add(given_day)
        db.session.commit()

        app.logger.info('%s description changed by %s', given_day, current_user)

        return redirect(url_for('manage_show', show_id=show_id))

    return render_template('manage_day_description.html', audition_day=given_day)


@app.route('/audition/<int:audition_id>', methods=['GET', 'POST'])
@login_required
def manage_audition(audition_id):
    audition = Audition.query.get(audition_id)

    if audition is None:
        flash('Audition not found', 'danger')
        return redirect(url_for('index'))

    if audition.auditionee != current_user and current_user not in audition.get_show().managers:
        app.logger.warn('%s does not have permission to view %s', current_user, audition)
        flash('You do not have permission to view this audition', 'danger')
        return redirect(url_for('index'))

    if audition.auditionee is None:
        app.logger.warn('%s requested %s but no auditionee', current_user, audition)
        flash('Audition is not booked by anyone', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if request.form['comment_text'] == '':
            flash('Your comment cannot be empty!', 'warning')
            return redirect(url_for('manage_audition', audition_id=audition_id))

        comment = Comment(time=datetime.now(), audition=audition, user=current_user,
                          comment_body=request.form['comment_text'])

        db.session.add(comment)
        db.session.commit()

        app.logger.info('%s posted new comment on %s', current_user, audition)
        return redirect(url_for('manage_audition', audition_id=audition_id))

    template_files = [os.path.basename(file)[:-3] for file in glob.glob('comment_template/*.md')]

    return render_template('audition.html' if current_user in audition.get_show().managers else 'my_audition.html',
                           show=audition.get_show(),
                           audition=audition, template_files=template_files)


@app.route('/audition/<int:audition_id>/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(audition_id, comment_id):
    comment = Comment.query.get(comment_id)

    if current_user not in comment.audition.get_show().managers:
        app.logger.warn('%s tried to edit %s but does not have permission', current_user, comment)
        flash('You do not have permission to edit this comment', 'danger')
        return redirect(url_for('index'))

    if comment.audition_id != audition_id:
        flash('Comment belongs to another audition', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        if request.form['comment_text'] == '':
            flash('Your comment cannot be empty!', 'warning')
            return redirect(url_for('manage_audition', audition_id=audition_id))

        comment.comment_body = request.form['comment_text']
        comment.edits += 1

        comment.last_edit_time = datetime.now()

        db.session.add(comment)
        db.session.commit()

        app.logger.info('%s edited by %s', comment, current_user)

        return redirect(url_for('manage_audition', audition_id=audition_id))

    return render_template('edit_comment.html', comment=comment)


@app.route('/comment/<int:comment_id>/delete')
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)

    if comment is None:
        flash('Comment not found', 'danger')
        return redirect(url_for('index'))

    if current_user not in comment.audition.get_show().managers:
        app.logger.warn('%s tried to delete %s but does not have permission', current_user, comment)
        flash('You do not have permission to delete this comment', 'danger')
        return redirect(url_for('index'))

    db.session.delete(comment)
    db.session.commit()

    app.logger.info('%s deleted comment %s', current_user, comment)

    return redirect(url_for('manage_audition', audition_id=comment.audition_id))


@app.route('/comment/<int:comment_id>/toggle_viewable')
@login_required
def toggle_comment_viewable(comment_id):
    comment = Comment.query.get(comment_id)

    if comment is None:
        flash('Comment not found', 'danger')
        return redirect(url_for('index'))

    if current_user not in comment.audition.get_show().managers:
        app.logger.warn('%s does not have permission to toggle view status for %s', current_user, comment)
        flash('You do not have permission to edit this comment', 'danger')
        return redirect(url_for('index'))

    if not comment.viewable_by_auditionee:
        comment.viewable_by_auditionee = True
        app.logger.info('%s made %s visible to %s', current_user, comment, comment.audition.auditionee)

        if comment.audition.auditionee.has_valid_email():
            message = Message('You have new audition feedback', recipients=[comment.audition.auditionee.email],
                              html=render_template('email/audition_feedback_posted.html', comment=comment))
            send_mail(message)

    else:
        comment.viewable_by_auditionee = False
        app.logger.info('%s hid %s from %s', current_user, comment, comment.audition.auditionee)

    db.session.add(comment)
    db.session.commit()

    return redirect(url_for('manage_audition', audition_id=comment.audition_id))


@app.route('/audition/<int:audition_id>/comment/template/<string:template_filename>')
@login_required
def get_comment_template(audition_id, template_filename):
    audition = Audition.query.get(audition_id)
    if audition is None:
        abort(404)

    if not os.path.isfile('comment_template/' + template_filename + '.md'):
        abort(404)

    with open('comment_template/' + template_filename + '.md') as template_file:
        return render_template_string(template_file.read(), audition=audition)


@app.route('/audition/<int:audition_id>/book', methods=['GET', 'POST'])
@login_required
def book_audition(audition_id):
    audition = Audition.query.get(audition_id)
    if audition is None:
        flash('Audition not found', 'danger')
        return redirect(url_for('index'))

    if audition.auditionee == current_user:
        app.logger.warn('%s tried to book %s but already booked by self', current_user, audition)
        flash('You have already booked this audition', 'warning')
        return redirect(url_for('index'))

    if audition.auditionee is not None:
        app.logger.warn('%s tried to book %s but booked by someone else', current_user, audition)
        flash('This audition is booked by someone else', 'warning')
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('confirm_book.html',
                               show=audition.audition_day.show,
                               audition=audition)

    # Don't let a user book an audition clashing with another one. Check every existing audition
    for user_audition in current_user.auditions:
        # If the days don't match then there's definitely no clash
        if audition.audition_day.date != user_audition.audition_day.date:
            continue

        # Otherwise check for intersection.
        # Credit to http://stackoverflow.com/questions/3721249/python-date-interval-intersection
        if (audition.start_time <= user_audition.start_time <= audition.end_time) \
                or (user_audition.start_time <= audition.start_time <= user_audition.end_time):

            app.logger.info('%s attempted to book %s for %s but it clashed with %s for %s',
                            current_user, audition, audition.get_show(), user_audition, user_audition.get_show())

            flash('Cannot book the selected audition as it clashes with another.', 'warning')
            return redirect(url_for('show', show_id=audition.audition_day_show_id))

    audition.auditionee = current_user
    db.session.add(audition)
    db.session.commit()

    app.logger.info('%s booked %s for %s', current_user, audition, audition.get_show())

    flash('Your audition has been booked. We look forward to seeing you soon', 'success')
    return redirect(url_for('my_auditions'))


@app.route('/audition/<int:audition_id>/cancel', methods=['GET', 'POST'])
@login_required
def cancel_audition(audition_id):
    audition = Audition.query.get(audition_id)
    if audition is None:
        flash('Audition not found', 'danger')
        return redirect(url_for('index'))

    if audition.auditionee is None:
        app.logger.warn('%s tried to cancel vacant %s', current_user, audition)
        flash('Requested audition is not booked and so cannot be cancelled', 'warning')
        return redirect(url_for('index'))

    if current_user != audition.auditionee and current_user not in audition.get_show().managers:
        app.logger.warn('%s tried to cancel %s but booked by someone else', current_user, audition)
        flash('You do not have permission to cancel that audition', 'danger')
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('confirm_cancel.html',
                               show=audition.audition_day.show,
                               audition=audition)

    if audition.auditionee != current_user:
        message = 'Audition cancelled'
    else:
        message = 'Your audition has been cancelled'

    audition.auditionee = None

    for comment in audition.comments:
        db.session.delete(comment)

    db.session.add(audition)
    db.session.commit()

    app.logger.info('%s cancelled audition %s for %s', current_user, audition, audition.get_show())

    flash(message, 'info')
    return redirect(url_for('my_auditions'))


@app.route('/help/markdown')
@login_required
def markdown_help():
    return render_template('popup/markdown_help.html')


@app.route('/profile')
def profile():
    return redirect(url_for('view_profile', user_id=current_user.id))


@app.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get(user_id)

    if user is None:
        flash('The requested user does not exist', 'danger')
        app.logger.warn('%s tried to view profile for user ID %s but it does not exist', current_user, user_id)
        return redirect(url_for('index'))

    if user.id != current_user.id:
        flash('You do not have permission to view that user\'s profile.', 'danger')
        app.logger.warn('%s tried to view profile for %s but does not have permission', current_user, user)
        return redirect(url_for('index'))

    return render_template('profile.html', user=user)


@app.route('/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user = User.query.get(user_id)

    if user is None:
        flash('The requested user does not exist', 'danger')
        app.logger.warn('%s tried to edit profile for user ID %s but it does not exist', current_user, user_id)
        return redirect(url_for('index'))

    if user.id != current_user.id:
        flash('You do not have permission to edit that user\'s profile.', 'danger')
        app.logger.warn('%s tried to edit profile for %s but does not have permission', current_user, user)
        return redirect(url_for('index'))

    if request.method == 'POST':
        if request.form['first_name'] == '' or request.form['last_name'] == '' or request.form['email'] == '':
            flash('Please fill out all fields')
            return redirect(url_for('edit_profile', user_id=user_id))

        if not validate_email(request.form['email']):
            flash('Please provide a valid email address', 'warning')
            return redirect(url_for('edit_profile', user_id=user_id))

        user.email = request.form['email']
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']

        db.session.add(user)
        db.session.commit()

        app.logger.info('%s edited profile for %s', current_user, user)

        flash('Changes saved', 'success')
        return redirect(url_for('view_profile', user_id=user_id))

    return render_template('edit_profile.html', user=user)
