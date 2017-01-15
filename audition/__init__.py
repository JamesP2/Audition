from flask import Flask
from flask_login import LoginManager
from flask_oauthlib.client import OAuth
from flaskext.markdown import Markdown

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

import audition.views
