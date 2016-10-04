from flask import Flask, g, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
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
        flash('Username or Password incorrect', 'error')
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
    return render_template('shows.html',
                           shows=Show.query.all())


@app.route('/me')
@login_required
def my_auditions():
    return render_template('myauditions.html',
                           user=current_user)


@app.route('/showauditions/<int:show_id>')
@login_required
def audition_slots(show_id):
    show = Show.query.get(show_id)

    if show is None:
        flash('Invalid show ID', 'error')
        return redirect(url_for('index'))

    return render_template('auditionslots.html',
                           show=show)


@app.route('/book/<int:slot_id>', methods=['GET', 'POST'])
@login_required
def book_slot(slot_id):
    slot = AuditionSlot.query.get(slot_id)
    if slot is None:
        flash('Slot not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('confirmslot.html',
                               show=slot.audition_day.show,
                               slot=slot)

    slot.auditionee = current_user
    db.session.add(slot)
    db.session.commit()

    flash('Your audition has been booked. We look forward to seeing you soon')
    return redirect(url_for('my_auditions'))