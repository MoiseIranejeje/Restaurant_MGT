from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Shop, Product, SubscriptionRequest, UserPackage, RedemptionRequest
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired
import math
import datetime

bp = Blueprint('buyer', __name__)

class SubscriptionForm(FlaskForm):
    amount = FloatField('Amount to Pay', validators=[DataRequired()])
    submit = SubmitField('Request Subscription')

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'buyer':
            return redirect(url_for('buyer.dashboard'))
        elif current_user.role == 'shop_admin':
            return redirect(url_for('shop.dashboard'))
        elif current_user.role == 'system_admin':
            return redirect(url_for('admin.dashboard'))
    return render_template('buyer/index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'buyer':
        return redirect(url_for('buyer.index'))

    packages = UserPackage.query.filter_by(user_id=current_user.id).filter(UserPackage.balance > 0).all()
    pending = SubscriptionRequest.query.filter_by(user_id=current_user.id, status='pending').all()

    return render_template('buyer/dashboard.html', packages=packages, pending=pending)

@bp.route('/search', methods=['GET', 'POST'])
def search_shop():
    if request.method == 'POST':
        code = request.form.get('shop_code')
        shop = Shop.query.filter_by(shop_code=code).first()
        if shop:
            return redirect(url_for('buyer.shop_profile', shop_id=shop.id))
        flash('Shop not found.')
    return render_template('buyer/search.html')

@bp.route('/shop/<int:shop_id>')
def shop_profile(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    return render_template('buyer/shop_profile.html', shop=shop)

@bp.route('/product/<int:product_id>/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe(product_id):
    product = Product.query.get_or_404(product_id)
    form = SubscriptionForm()

    if form.validate_on_submit():
        amount = form.amount.data
        if amount < product.price_per_unit:
            flash(f'Amount must be at least {product.price_per_unit}')
            return render_template('buyer/subscribe.html', form=form, product=product)

        units = math.floor(amount / product.price_per_unit)

        req = SubscriptionRequest(
            user_id=current_user.id,
            shop_id=product.shop_id,
            product_id=product.id,
            amount_paid=amount,
            calculated_units=units
        )
        db.session.add(req)
        db.session.commit()
        flash('Subscription request sent! Waiting for shop confirmation.')
        return redirect(url_for('buyer.dashboard'))

    return render_template('buyer/subscribe.html', form=form, product=product)

@bp.route('/redeem/<int:package_id>', methods=['GET', 'POST'])
@login_required
def redeem(package_id):
    package = UserPackage.query.get_or_404(package_id)
    if package.user_id != current_user.id or package.balance < 1:
        flash("Invalid package or insufficient balance")
        return redirect(url_for('buyer.dashboard'))

    return render_template('buyer/redeem.html', package=package)

@bp.route('/api/request_redemption/<int:package_id>', methods=['POST'])
@login_required
def request_redemption(package_id):
    package = UserPackage.query.get_or_404(package_id)
    if package.user_id != current_user.id or package.balance < 1:
        return jsonify({'status': 'error', 'message': 'Invalid package'}), 400

    req = RedemptionRequest(
        user_id=current_user.id,
        shop_id=package.shop_id,
        product_id=package.product_id,
        units_requested=1
    )
    db.session.add(req)
    db.session.commit()

    return jsonify({'status': 'success', 'request_id': req.id})

@bp.route('/api/check_redemption_status/<int:request_id>')
@login_required
def check_redemption_status(request_id):
    req = RedemptionRequest.query.get(request_id)
    if req and req.status == 'approved':
        return jsonify({'status': 'approved'})
    elif req and req.status == 'rejected':
         return jsonify({'status': 'rejected'})
    return jsonify({'status': 'pending'})
