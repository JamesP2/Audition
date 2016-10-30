DEBUG = True
TESTING = False

SERVER_NAME = 'localhost'

# Be sure to install pymysql if you intend to use this as written in this example
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://auditionslot:auditionslot@127.0.0.1:3306/auditionslot'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

SECRET_KEY = 'SECRET'

FACEBOOK_APP_ID = 'YOUR APP ID'
FACEBOOK_APP_SECRET = 'SECRET'
