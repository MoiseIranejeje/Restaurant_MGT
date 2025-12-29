from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app import db
from app.models import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length

bp = Blueprint('auth', __name__)

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=5, message="Password must be at least 5 characters long.")])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class DeleteAccountForm(FlaskForm):
    password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Delete Account')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5, message="Password must be at least 5 characters long.")])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('buyer', 'Buyer'), ('shop_admin', 'Shop Owner')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('buyer.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.role == 'system_admin':
                next_page = url_for('admin.dashboard')
            elif user.role == 'shop_admin':
                next_page = url_for('shop.dashboard')
            else:
                next_page = url_for('buyer.index')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('buyer.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('Incorrect old password.')
            return redirect(url_for('auth.change_password'))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been updated.')
        return redirect(url_for('buyer.index')) # Or respective dashboard
    return render_template('auth/change_password.html', form=form)

@bp.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash('Incorrect password.')
            return redirect(url_for('auth.delete_account'))

        # Soft delete
        current_user.is_deleted = True
        current_user.email = f"deleted_{current_user.id}_{current_user.email}"
        current_user.username = f"deleted_{current_user.id}_{current_user.username}"
        db.session.commit()
        logout_user()
        flash('Your account has been deleted.')
        return redirect(url_for('buyer.index'))
    return render_template('auth/delete_account.html', form=form)
