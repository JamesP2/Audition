from flask import Flask, g, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)

    username = db.Column(db.String(30))
    password = db.Column(db.String(80))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)


class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def get_audition_dates_string(self):
        if len(self.audition_days) == 0:
            return 'No audition dates yet'

        date_string = ''

        for day in self.audition_days:
            date_string += ', ' + day.get_date_string()

        return date_string[2:]

    def get_audition_slots(self):
        slots = []

        for day in self.audition_days:
            for slot in day.audition_slots:
                slots.append(slot)

        return slots


class AuditionDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)

    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    show = db.relationship('Show', backref='audition_days')

    def get_date_string(self):
        return self.date.strftime("%A %d %B %Y")


class AuditionSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Time)

    audition_day_id = db.Column(db.Integer, db.ForeignKey('audition_day.id'), nullable=False)
    audition_day = db.relationship('AuditionDay', backref='audition_slots')

    auditionee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    auditionee = db.relationship('User', backref='audition_slots')

    def get_date_time_string(self):
        return self.audition_day.get_date_string() + self.get_time_string()

    def get_time_string(self):
        return str(self.time)

    def is_available(self):
        return self.auditionee is not None


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def create_models():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
def audition_slots(show_id):
    show = Show.query.get(show_id)

    if show is None:
        flash('Invalid show ID', 'error')
        return redirect(url_for('index'))

    return render_template('auditionslots.html',
                           show=show)


@app.route('/book/<int:slot_id>')
def book_slot(slot_id):
    pass


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


if __name__ == '__main__':
    app.run()
