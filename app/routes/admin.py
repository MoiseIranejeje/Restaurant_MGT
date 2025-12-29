from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Shop, User
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import uuid
import datetime

bp = Blueprint('admin', __name__, url_prefix='/admin')

class CreateShopForm(FlaskForm):
    name = StringField('Shop Name', validators=[DataRequired()])
    owner_username = StringField('Owner Username', validators=[DataRequired()])
    submit = SubmitField('Create Shop')

@bp.before_request
@login_required
def before_request():
    if current_user.role != 'system_admin':
        flash('Access denied.')
        return redirect(url_for('buyer.index'))

@bp.route('/dashboard')
def dashboard():
    shops = Shop.query.all()
    return render_template('admin/dashboard.html', shops=shops)

@bp.route('/create_shop', methods=['GET', 'POST'])
def create_shop():
    form = CreateShopForm()
    if form.validate_on_submit():
        owner = User.query.filter_by(username=form.owner_username.data).first()
        if not owner or owner.role != 'shop_admin':
            flash('Invalid owner username or user is not a Shop Owner.')
            return redirect(url_for('admin.create_shop'))

        shop_code = str(uuid.uuid4())[:8].upper()
        # Set 30-day subscription
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        shop = Shop(name=form.name.data, owner=owner, shop_code=shop_code, subscription_expires_at=expires_at)
        db.session.add(shop)
        db.session.commit()
        flash(f'Shop created successfully! Code: {shop_code}')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_shop.html', form=form)
