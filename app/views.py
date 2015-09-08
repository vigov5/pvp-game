from functools import wraps
from flask import render_template, flash, redirect, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, rc
from forms import LoginForm, SignupForm, CreateGameForm, JoinGameForm
from wtforms.ext.sqlalchemy.orm import model_form
from flask_wtf import Form
from models import User, Game, Deck, Fact, get_object_or_404
from flask.ext.admin.contrib.sqla import ModelView
from game_object import GameObject

@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(userid):
    return User.query.get(int(userid))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_admin():
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    games = Game.query.order_by(Game.id.desc()).limit(20)
    create_form = CreateGameForm(g.user)
    join_form = JoinGameForm(g.user)
    if join_form.validate_on_submit():
        game = Game.query.get(join_form.game_id.data)
        game.guest_id = g.user.id
        game.status = 'joined'
        db.session.add(game)
        db.session.commit()
        go = GameObject().from_game(game)
        rc.set("g%d" % game.id, go.to_json())
        return redirect(url_for('game', game_id=game.id))
    elif create_form.validate_on_submit():
        host_player = User.query.get(create_form.user_id.data)
        new_game = Game(host_player, deck=create_form.deck.data, reversed=create_form.reversed.data)
        db.session.add(new_game)
        db.session.commit()
        go = GameObject().from_game(new_game)
        rc.set("g%d" % new_game.id, go.to_json())
        return redirect(url_for('game', game_id=new_game.id))
    return render_template(
        'index.html',
        user=g.user,
        create_form=create_form,
        page='index',
        games=games
    )

@app.route('/game/<int:game_id>', methods = ['GET', 'POST'])
@login_required
def game(game_id=None):
    game = get_object_or_404(Game, Game.id == game_id)
    host_player = None
    guest_player = None
    if game.status == 'canceled':
        return redirect(url_for('index'))
    if game.status == 'created':
        host_player = get_object_or_404(User, User.id == game.host_id)
    if game.status == 'joined':
        host_player = get_object_or_404(User, User.id == game.host_id)
        guest_player = get_object_or_404(User, User.id == game.guest_id)
    role = 'watcher'
    if g.user.id == game.host_id:
        role = 'host'
    elif g.user.id == game.guest_id:
        role = 'join'

    return render_template(
        'game.html',
        game=game,
        role=role,
        host_player=host_player,
        guest_player=guest_player,
        page='game'
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        new_user = User(form.username.data, form.email.data, form.password.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(username = form.username.data).first()
        login_user(user)
        flash('Logged in successfully.', category='success')
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', category='success')
    return redirect(url_for('index'))

@app.route('/profile', methods = ['GET', 'POST'])
@app.route('/profile/<int:user_id>', methods = ['GET', 'POST'])
@login_required
def profile(user_id = None):
    if g.user is not None and g.user.is_authenticated():
        if user_id is None:
            return render_template('profile.html', user=g.user)
        else:
            user = User.query.get(user_id)
            if user:
                return render_template('profile.html', user=user)
            else:
                return redirect(url_for('index'))
    else:
        if user_id is None:
            return redirect(url_for('index'))
        else:
            user = User.query.get(user_id)

@app.route('/profile/edit', methods = ['GET', 'POST'])
@login_required
def edit_profile():
    if g.user is not None and g.user.is_authenticated():
        UserForm = model_form(User, db_session=db.session,
            base_class=Form, only=['email', 'name']
        )
        model = User.query.get(g.user.id)
        form = UserForm(request.form, model)

        if form.validate_on_submit():
            form.populate_obj(model)
            db.session.add(model)
            db.session.commit()
            flash('Profile updated', category='success')
            return redirect(url_for('profile'))
        return render_template('edit_profile.html', user=g.user, form=form)
    else:
        return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# admin pages
class UserView(ModelView):
    # Disable model creation
    can_create = False

    # Override displayed fields
    column_list = ('username', 'name', 'email', 'role')
    column_filters = ('username', 'name', 'email')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(UserView, self).__init__(User, session, **kwargs)

    def is_accessible(self):
        return g.user.is_admin()

class DeckView(ModelView):

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(DeckView, self).__init__(Deck, session, **kwargs)

    def is_accessible(self):
        return g.user.is_admin()

class FactView(ModelView):

    column_filters = ('front', 'back')
    column_list = ('front', 'back', 'decks_used')

    def __init__(self, session, **kwargs):
        # You can pass name and other parameters if you want to
        super(FactView, self).__init__(Fact, session, **kwargs)

    def is_accessible(self):
        return g.user.is_admin()
