from flask import g, render_template, request, session, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from flask_oauthlib.client import OAuthException
from audition import app, facebook, login_manager
from audition.models import *
from datetime import datetime


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
    app.logger.debug('Response from facebook: %s',  resp)

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
        new_username = (me.data['first_name'] + '_' + me.data['last_name']).lower()
        count = 1

        while User.query.filter_by(username=new_username).first() is not None:
            new_username = (me.data['first_name'] + '_' + me.data['last_name'] + str(count)).lower()
            count += 1

        new_user = User(first_name=me.data['first_name'], last_name=me.data['last_name'], username=new_username,
                        email=me.data['email'] if 'email' in me.data.keys() else '')
        new_user.providers.append(UserProvider(user_uid=me.data['id'], provider_id='facebook',
                                               email=me.data['email'] if 'email' in me.data.keys() else ''))

        db.session.add(new_user)
        db.session.commit()

        app.logger.info('%s Logging in via Facebook (new user)', new_user)
        login_user(new_user)

    return redirect(request.args.get('next') or url_for('index'))


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.before_request
def before_request():
    g.user = current_user


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

    if audition.auditionee is None:
        app.logger.warn('%i requested but no auditionee', audition_id)
        flash('Audition is not booked by anyone', 'danger')
        return redirect(url_for('index'))

    if audition.auditionee != current_user and current_user not in audition.get_show().managers:
        app.logger.warn('%s does not have permission to view %s', current_user, audition)
        flash('You do not have permission to view this audition', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        comment = Comment(time=datetime.now(), audition=audition, user=current_user,
                          comment_body=request.form['comment_text'])

        db.session.add(comment)
        db.session.commit()

        app.logger.info('%s posted new comment on %s', current_user, audition)
        return redirect(url_for('manage_audition', audition_id=audition_id))

    return render_template('audition.html' if current_user in audition.get_show().managers else 'my_audition.html',
                           show=audition.get_show(),
                           audition=audition)


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

    comment.viewable_by_auditionee = not comment.viewable_by_auditionee

    db.session.add(comment)
    db.session.commit()

    app.logger.warn('%s toggled view status for %s', current_user, comment)

    return redirect(url_for('manage_audition', audition_id=comment.audition_id))


@app.route('/audition/<int:audition_id>/book', methods=['GET', 'POST'])
@login_required
def book_audition(audition_id):
    audition = Audition.query.get(audition_id)
    if audition is None:
        flash('Audition not found', 'danger')
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('confirm_book.html',
                               show=audition.audition_day.show,
                               audition=audition)

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

    if request.method == 'GET':
        return render_template('confirm_cancel.html',
                               show=audition.audition_day.show,
                               audition=audition)

    audition.auditionee = None

    for comment in audition.comments:
        db.session.delete(comment)

    db.session.add(audition)
    db.session.commit()

    app.logger.info('%s cancelled audition %s for %s', current_user, audition, audition.get_show())

    flash('Your audition has been cancelled.', 'info')
    return redirect(url_for('my_auditions'))
