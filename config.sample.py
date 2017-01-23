import logging

DEBUG = True
TESTING = False

# Setting this to False will stop Facebook users from logging in and display a landing page to anonymous users
SITE_ENABLED = True

# Be sure to install pymysql if you intend to use this as written in this example
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://auditionslot:auditionslot@127.0.0.1:3306/auditionslot'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

SECRET_KEY = 'SECRET'

FACEBOOK_APP_ID = 'YOUR APP ID'
FACEBOOK_APP_SECRET = 'SECRET'

OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 120

LOG_ENABLED = True
LOG_LEVEL = logging.INFO
LOG_FILE = 'audition.log'

MAIL_ENABLE = False

MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None

MAIL_FROM = ('Your Name', 'yourmail@example.com')
MAIL_BCC = None

WARN_EMAIL = True
