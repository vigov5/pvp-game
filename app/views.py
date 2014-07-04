from flask import render_template, flash, redirect, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, SignupForm
from wtforms.ext.sqlalchemy.orm import model_form
from flask_wtf import Form
from models import User, ROLE_USER, ROLE_ADMIN

@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(userid):
    return User.query.get(int(userid))

@app.route('/')
@app.route('/index')
def index():
    return render_template(
        'index.html',
        user=g.user
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        new_user = User(form.username.data, form.email.data, form.password.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        redirect(request.args.get('next') or url_for('index'))
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
