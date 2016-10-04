from flask_sqlalchemy import SQLAlchemy
from audition import app

db = SQLAlchemy(app)


def init_db():
    """ Initialise the Database with all imported models """
    import audition.models
    db.create_all()
