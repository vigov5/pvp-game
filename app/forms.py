from flask_wtf import Form
from wtforms import TextField, SubmitField, validators, PasswordField, HiddenField, BooleanField
from models import User, Game, Deck
from wtforms.ext.sqlalchemy.fields import QuerySelectField

class SignupForm(Form):
    username = TextField('Username',  [
        validators.Required('Please enter your username.'),
        validators.Length(max=30, message='Username is at most 30 characters.'),
    ])
    email = TextField('Email',  [
        validators.Required('Please enter your email address.'),
        validators.Email('Please enter your email address.')
    ])
    password = PasswordField('Password', [
        validators.Required('Please enter a password.'),
        validators.Length(min=6, message='Passwords is at least 6 characters.'),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Create account')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(username = self.username.data).first()
        if user:
            self.username.errors.append('That username is already taken.')
            return False
        else:
            return True

class LoginForm(Form):
    username = TextField('Username',  [
        validators.Required('Please enter your username.'),
        validators.Length(max=30, message='Username is at most 30 characters.'),
    ])
    password = PasswordField('Password', [
        validators.Required('Please enter a password.'),
        validators.Length(min=6, message='Passwords is at least 6 characters.'),
    ])
    submit = SubmitField('Sign In')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
    
        user = User.query.filter_by(username = self.username.data).first()
        if user and user.check_password(self.password.data):
            return True
        else:
            self.password.errors.append('Invalid e-mail or password')
            return False

def deck_query():
    return Deck.query.all()

class CreateGameForm(Form):
    user_id = HiddenField('user_id')
    submit = SubmitField('Create Game')
    deck = QuerySelectField(query_factory=deck_query, get_label='name')
    reversed = BooleanField('Is Open')

    def __init__(self, current_user, *args, **kwargs):
        self.current_user_id = current_user.id
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.get(self.user_id.data)
        if not user or user.id != self.current_user_id:
            self.user_id.errors.append('Invalid user')
            return False
        else:
            return True

class JoinGameForm(Form):
    game_id = HiddenField('game_id')
    user_id = HiddenField('user_id')
    submit = SubmitField('Join Game')

    def __init__(self, current_user, *args, **kwargs):
        self.current_user_id = current_user.id
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        game = Game.query.get(self.game_id.data)
        if not game or game.status != 'created':
            return False
        else:
            return True
