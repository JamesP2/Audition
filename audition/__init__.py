from flask import Flask, g, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_required, current_user, login_user, logout_user

app = Flask(__name__)
app.config.from_pyfile('../config.py')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# import audition.views
