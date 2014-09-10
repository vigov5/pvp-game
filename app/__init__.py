import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from config import basedir
from flask.ext.admin import Admin

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models

admin = Admin(app)
admin.add_view(views.UserView(db.session, name='Users'))
admin.add_view(views.DeckView(db.session, name='Decks'))
admin.add_view(views.FactView(db.session, name='Facts'))
