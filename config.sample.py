import logging

# Debug/Test - NEVER true in production!
DEBUG = True
TESTING = False

# Setting this to False will stop Facebook users from logging in and display a landing page to anonymous users
SITE_ENABLED = True

# Be sure to install pymysql if you intend to use this as written in this example
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://auditionslot:auditionslot@127.0.0.1:3306/auditionslot'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

# Set a unique secret key!
SECRET_KEY = 'SECRET'

# Facebook App Information for FB auth
FACEBOOK_APP_ID = 'YOUR APP ID'
FACEBOOK_APP_SECRET = 'SECRET'

# OAuth2 token expiry (120 is usually fine)
OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 120

# Logging
LOG_ENABLED = True
LOG_LEVEL = logging.INFO
LOG_FILE = 'audition.log'

# Whether or not to send mail to auditionees (needed for production)
MAIL_ENABLE = False

# Mailserver information
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None

# Sender details
MAIL_FROM = ('Your Name', 'yourmail@example.com')

# Optional BCC
MAIL_BCC = None

# Enable invalid email warnings for users?
WARN_EMAIL = True

# Google Analytics Enable
GANALYTICS_ENABLE = False

# Google Analytics Tracking ID
GANALYTICS_ID = 'YOUR_TRACKING_ID'