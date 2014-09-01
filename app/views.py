from flask import render_template, flash, redirect, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, SignupForm, CreateGameForm
from wtforms.ext.sqlalchemy.orm import model_form
from flask_wtf import Form
from models import User, Game, ROLE_USER, ROLE_ADMIN, get_object_or_404

@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(userid):
    return User.query.get(int(userid))

@app.route('/')
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    form = CreateGameForm(g.user)
    if form.validate_on_submit():
        host_player = User.query.get(form.user_id.data)
        new_game = Game(host_player)
        db.session.add(new_game)
        db.session.commit()
        return redirect(url_for('game', game_id=new_game.id))
    return render_template(
        'index.html',
        user=g.user,
        create_form=form
    )

@app.route('/game/<int:game_id>', methods = ['GET', 'POST'])
@login_required
def game(game_id=None):
    game = get_object_or_404(Game, Game.id == game_id)
    host_player = None
    guest_player = None
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
