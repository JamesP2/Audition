import html, re

from audition.database import db
from hashlib import md5
from urllib.parse import quote_plus
from werkzeug.security import check_password_hash, generate_password_hash

show_managers = db.Table('show_managers',
                         db.Column('show_id', db.Integer, db.ForeignKey('show.id')),
                         db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
                         )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)

    username = db.Column(db.String(30))
    password = db.Column(db.String(80))
    email = db.Column(db.String(200))

    managed_shows = db.relationship('Show', secondary=show_managers,
                                    backref='managers')

    def is_authenticated(self):
        """ Is the user authenticated? (always true since any user object is authed) """
        return True

    def is_active(self):
        """ Is the user active? (always true since any user object is active) """
        return True

    def is_anonymous(self):
        """ Is the user anon? (always false since any logged in user cannot be anonymous) """
        return False

    def get_id(self):
        """ Get the ID of the user """
        return self.id

    def check_password(self, password):
        """ Check the given password with the hashed password in the database """
        return self.password is not None and self.password != '' and check_password_hash(self.password, password)

    def set_password(self, password):
        """ Generate a password hash based on the given password """
        self.password = generate_password_hash(password)

    def get_full_name(self):
        """ Return the full name of the user """
        return self.first_name + ' ' + self.last_name

    def get_avatar_url(self):
        """ Return an URL for an avatar. If a FB provider exists use that, otherwise use gravatar """
        if len(self.providers) > 0:
            for provider in self.providers:
                if provider.provider_id == 'facebook':
                    return 'http://graph.facebook.com/' + provider.user_uid + '/picture'

        email = self.email if self.email is not None else ''

        return 'https://www.gravatar.com/avatar/' + md5(str.encode(email)).hexdigest() + '?d=retro'

    def auditioning_for(self, show):
        """ Check if the user is auditioning for the given show """
        for slot in self.auditions:
            if slot.audition_day_show_id == show.id:
                return True

        return False


class UserProvider(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    provider_id = db.Column(db.String(20), primary_key=True)

    user = db.relationship('User', backref='providers')
    email = db.Column(db.String(200))

    user_uid = db.Column(db.String(200))


class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    description = db.Column(db.String(4000))

    def get_audition_dates_string(self):
        """ Get a string of all the dates that the show is running auditions for """
        if len(self.audition_days) == 0:
            return 'No audition dates yet'

        date_string = ''

        for day in self.audition_days:
            date_string += ', ' + day.get_date_string()

        return date_string[2:]

    def get_auditions(self):
        """ Get all auditions from all audition days for the given show """
        auditions = []

        for day in self.audition_days:
            for audition in day.auditions:
                auditions.append(audition)

        return auditions

    def has_day(self, date):
        """ Check to see if the show already has the given day """
        for day in self.audition_days:
            if day.date == date:
                return True


class AuditionDay(db.Model):
    date = db.Column(db.Date, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), primary_key=True)

    show = db.relationship('Show', backref='audition_days')

    description = db.Column(db.String(4000))

    def get_date_string(self):
        """ Get date string in the form of Day D Month Year """
        return self.date.strftime('%A %d %B %Y')

    def get_short_date_string(self):
        """ Get date string in the form of DD/MM/YY """
        return self.date.strftime('%d/%m/%y')


class Audition(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    audition_day_show_id = db.Column(db.Integer)
    audition_day_date = db.Column(db.Date)

    audition_day = db.relationship('AuditionDay', backref='auditions')

    auditionee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    auditionee = db.relationship('User', backref='auditions')

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['audition_day_show_id', 'audition_day_date'],
            ['audition_day.show_id', 'audition_day.date']
        ),
        {}
    )

    __mapper_args__ = {
        'order_by': start_time
    }

    def get_date_time_string(self):
        """ Get the date time string of this slot in the form of DD/MM/YY HH:MM - HH:MM"""
        return self.audition_day.get_short_date_string() \
               + ' ' + self.get_start_time_string() + ' - ' + self.get_end_time_string()

    def get_long_date_time_string(self):
        """ Get the date time string of this slot in the form of 'Day D Month Year' HH:MM - HH:MM"""
        return self.audition_day.get_date_string() \
               + ' ' + self.get_start_time_string() + ' - ' + self.get_end_time_string()

    def get_start_time_string(self):
        """ Get the start time in the form HH:MM """
        return self.start_time.strftime('%H:%M')

    def get_end_time_string(self):
        """ Get the end time in the form HH:MM """
        return self.end_time.strftime('%H:%M')

    def get_show(self):
        """ Get the show for this audition """
        return self.audition_day.show

    def is_available(self):
        """ Return True if the slot is not booked """
        return self.auditionee is None

    def has_feedback_for_auditionee(self):
        """ Return True if a comment has been set to be viewable by the auditionee """
        for comment in self.comments:
            if comment.viewable_by_auditionee:
                return True

        return False

    def __repr__(self):
        return 'audition %s' % str(self.id)

    def __str__(self):
        return 'Audition %s - %s (%s)' \
               % (str(self.start_time), str(self.end_time),
                  'Available' if self.is_available() else 'Unavailable')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    time = db.Column(db.DateTime)
    last_edit_time = db.Column(db.DateTime)

    edits = db.Column(db.Integer, default=0)

    comment_body = db.Column(db.String(2000))

    audition_id = db.Column(db.Integer, db.ForeignKey('audition.id'))
    audition = db.relationship('Audition', backref='comments')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='comments')

    viewable_by_auditionee = db.Column(db.Boolean, default=False)

    __mapper_args__ = {
        'order_by': time
    }

    def get_date_string(self):
        return self.time.strftime('%d/%m/%y')

    def get_time_string(self):
        return self.time.strftime('%H:%M')
