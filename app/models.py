import hashlib
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(50))
    email = db.Column(db.String(45))
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

    def __init__(self, username, email, password):
        self.username = username
        self.name = username
        self.email = email.lower()
        self.set_password(password)
         
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

    def getAvatar(self, size = 160):
        email_hash = hashlib.md5(self.email).hexdigest()
        return "http://www.gravatar.com/avatar/%s?d=mm&s=%d" % (email_hash, size)


class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30))
    description = db.Column(db.Text)
    members = db.relationship('User', backref = 'team', lazy = 'dynamic')

    def __repr__(self):
        return '<Team %r>' % (self.name)
