from flask import g, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from audition import app, login_manager
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
