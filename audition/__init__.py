from flask import Flask
from flask_login import LoginManager
from flask_oauthlib.client import OAuth
from flaskext.markdown import Markdown
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_pyfile('../config.py')

markdown = Markdown(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

oauth = OAuth()

facebook = oauth.remote_app('facebook',
                            base_url='https://graph.facebook.com/',
                            request_token_url=None,
                            access_token_url='/oauth/access_token',
                            authorize_url='https://www.facebook.com/dialog/oauth',
                            consumer_key=app.config['FACEBOOK_APP_ID'],
                            consumer_secret=app.config['FACEBOOK_APP_SECRET'],
                            request_token_params={'scope': 'email'}
)

if app.config['LOG_ENABLED']:
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(funcName)s - %(message)s')
    handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=1000000, backupCount=2, encoding='utf-8')
    handler.setFormatter(formatter)
    app.logger.setLevel(app.config['LOG_LEVEL'])
    app.logger.addHandler(handler)
    app.logger.info('Application started')

import audition.views
