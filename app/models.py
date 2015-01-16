import hashlib
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import exc
from werkzeug.exceptions import abort
from sqlalchemy.schema import UniqueConstraint

ROLE_USER = 0
ROLE_ADMIN = 1

def get_object_or_404(model, *criterion):
    """ Snippet byVitaliy Shishorin, http://flask.pocoo.org/snippets/115/"""
    try:
        return model.query.filter(*criterion).one()
    except exc.NoResultFound, exc.MultipleResultsFound:
        abort(404)

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key = True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    guest_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    host_point = db.Column(db.Integer)
    guest_point = db.Column(db.Integer)
    status = db.Column(db.String(20))
    host_player = db.relationship('User', backref = 'hosted_game', primaryjoin='User.id==Game.host_id')
    guest_player = db.relationship('User', backref = 'joined_game', primaryjoin='User.id==Game.guest_id')
    reversed = db.Column(db.Boolean, default=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'))

    def __init__(self, host, deck=None, reversed=False):
        self.host_id = host.id
        self.guest_id = None
        self.status = 'created'
        self.host_point = 0
        self.guest_point = 0
        self.reversed = reversed
        self.deck = deck

    def print_status(self):
        if self.status == 'created':
            return '<span class="label label-primary">Created</span>'
        if self.status == 'joined':
            return '<span class="label label-warning">Ready</span>'
        if self.status == 'started':
            return '<span class="label label-success">Started</span>'
        if self.status == 'ended':
            return '<span class="label label-info">Ended</span>'
        if self.status == 'canceled':
            return '<span class="label label-default">Canceled</span>'
        return '<span class="label label-muted">Unknown</span>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True, nullable = False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(50))
    email = db.Column(db.String(45))
    role = db.Column(db.SmallInteger, default = ROLE_USER)

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

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def is_normal_user(self):
        return self.role == ROLE_USER


class Fact(db.Model):
    __tablename__ = 'facts'
    id = db.Column(db.Integer, primary_key = True)
    front = db.Column(db.String(255), unique = True, nullable = False)
    back = db.Column(db.Text)

    def __repr__(self):
        return '<Fact %r>' % (self.front)

    def __str__(self):
        return '%s' % (self.front)

    def __init__(self, front="", back="", deck=None):
        self.front = front
        self.back = back
        self.decks_used.append(deck)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

    def __repr__(self):
        return '<Category %r>' % (self.name)


class Deck(db.Model):
    __tablename__ = 'decks'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    data = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    facts = db.relationship('Fact', secondary='deck_facts', backref='decks_used')
    games_used = db.relationship('Game', backref = 'deck', lazy = 'dynamic')

    def __repr__(self):
        return '<Deck %r %r>' % (self.name, self.data)

    def __str__(self):
        return '%s' % (self.name)

    def __init__(self, name="", data=""):
        self.name = name
        self.data = data

class Sentence(db.Model):
    __tablename__ = 'sentences'
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.Text)
    meaning_en = db.Column(db.Text)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'))

    def __repr__(self):
        return '<Sentence %r>' % (self.content)

    def __init__(self, content, meaning_en):
        self.content = content
        self.meaning_en = meaning_en

class DeckInfo(db.Model):
    __tablename__ = 'deck_facts'
    id = db.Column(db.Integer, primary_key = True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'))
    fact_id = db.Column(db.Integer, db.ForeignKey('facts.id'))
    fact = db.relationship('Fact', backref=db.backref('fact_info', lazy = 'dynamic'))
    deck = db.relationship('Fact', backref=db.backref('deck_info', lazy = 'dynamic'))
    UniqueConstraint('deck_id', 'fact_id', name='deck_fact')
