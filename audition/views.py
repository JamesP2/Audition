import sys
from flask import g, render_template, request, session, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from flask_oauthlib.client import OAuthException
from audition import app, facebook, login_manager
from audition.models import *


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
        flash('Username or Password incorrect', 'danger')
        return redirect(url_for('login'))

    login_user(user, remember=remember_me)

    return redirect(request.args.get('next') or url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/facebookLogin')
def facebook_login():
    callback_url = url_for('facebook_authorized',
                           next=request.args.get('next') or request.referrer or None,
                           _external=True)

    return facebook.authorize(callback=callback_url)


@app.route('/facebookAuthorized')
def facebook_authorized():
    resp = facebook.authorized_response()

    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )

    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message

    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me', data={
        'fields': 'first_name,last_name,id,email'
    })

    provider = UserProvider.query.filter_by(user_uid=me.data['id'], provider_id='facebook').first()

    if provider is not None and provider.user is not None:
        login_user(provider.user)

    else:
        new_username = (me.data['first_name'] + '_' + me.data['last_name']).lower()
        count = 1

        while User.query.filter_by(username=new_username).first() is not None:
            new_username = (me.data['first_name'] + '_' + me.data['last_name'] + str(count)).lower()
            count += 1

        new_user = User(first_name=me.data['first_name'], last_name=me.data['last_name'], username=new_username,
                        email=me.data['email'])
        new_user.providers.append(UserProvider(user_uid=me.data['id'], provider_id='facebook', email=me.data['email']))

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

    return redirect(request.args.get('next') or url_for('index'))


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.before_request
def before_request():
    g.user = current_user


@app.route('/')
@login_required
def index():
    return render_template('index.html',
                           shows=Show.query.all())


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


@app.route('/audition/<audition_id>/book', methods=['GET', 'POST'])
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
    db.session.add(audition)
    db.session.commit()

    flash('Your audition has been cancelled.', 'info')
    return redirect(url_for('my_auditions'))
