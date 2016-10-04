from audition.database import db
from werkzeug.security import check_password_hash, generate_password_hash


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

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name


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

    def has_day(self, date):
        for day in self.audition_days:
            if day.date == date:
                return True


class AuditionDay(db.Model):
    date = db.Column(db.Date, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), primary_key=True)

    show = db.relationship('Show', backref='audition_days')

    def get_date_string(self):
        return self.date.strftime('%A %d %B %Y')

    def get_short_date_string(self):
        return self.date.strftime('%d/%m/%y')


class AuditionSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    audition_day_show_id = db.Column(db.Integer)
    audition_day_date = db.Column(db.Date)

    audition_day = db.relationship('AuditionDay', backref='audition_slots')

    auditionee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    auditionee = db.relationship('User', backref='audition_slots')

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
        return self.audition_day.get_short_date_string() \
               + ' ' + self.get_start_time_string() + ' - ' + self.get_end_time_string()

    def get_long_date_time_string(self):
        return self.audition_day.get_date_string() \
               + ' ' + self.get_start_time_string() + ' - ' + self.get_end_time_string()

    def get_start_time_string(self):
        return self.start_time.strftime('%H:%M')

    def get_end_time_string(self):
        return self.end_time.strftime('%H:%M')

    def is_available(self):
        return self.auditionee is None

    def __repr__(self):
        return 'audition %s' % str(self.id)

    def __str__(self):
        return 'Audition Slot %s - %s (%s)' \
               % (str(self.start_time), str(self.end_time),
                  'Available' if self.is_available() else 'Unavailable')
