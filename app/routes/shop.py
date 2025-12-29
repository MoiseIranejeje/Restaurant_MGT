from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Shop, Product, SubscriptionRequest, RedemptionRequest
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired
from app.utils import verify_password_required
import datetime

bp = Blueprint('shop', __name__, url_prefix='/shop')

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    price_per_unit = FloatField('Price per Unit', validators=[DataRequired()])
    unit_name = StringField('Unit Name (e.g. Plate)', validators=[DataRequired()])
    submit = SubmitField('Save Product')

@bp.before_request
@login_required
def before_request():
    if current_user.role != 'shop_admin':
        flash('Access denied.')
        return redirect(url_for('buyer.index'))

@bp.route('/dashboard')
def dashboard():
    shop = Shop.query.filter_by(owner_id=current_user.id).first()
    if not shop:
        return render_template('shop/no_shop.html')

    products = Product.query.filter_by(shop_id=shop.id).all()
    pending_requests = SubscriptionRequest.query.filter_by(shop_id=shop.id, status='pending').all()
    redemption_requests = RedemptionRequest.query.filter_by(shop_id=shop.id, status='pending').all()

    return render_template('shop/dashboard.html', shop=shop, products=products, requests=pending_requests, redemptions=redemption_requests)

@bp.route('/product/add', methods=['GET', 'POST'])
def add_product():
    shop = Shop.query.filter_by(owner_id=current_user.id).first()
    if not shop:
        return redirect(url_for('shop.dashboard'))

    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            shop_id=shop.id,
            name=form.name.data,
            description=form.description.data,
            price_per_unit=form.price_per_unit.data,
            unit_name=form.unit_name.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added.')
        return redirect(url_for('shop.dashboard'))
    return render_template('shop/edit_product.html', form=form, title="Add Product")

@bp.route('/confirm_payment/<int:request_id>', methods=['POST'])
@login_required
@verify_password_required
def confirm_payment(request_id):
    req = SubscriptionRequest.query.get_or_404(request_id)
    if req.shop.owner_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('shop.dashboard'))

    from app.models import UserPackage

    req.status = 'approved'
    req.processed_at = datetime.datetime.utcnow()

    package = UserPackage.query.filter_by(user_id=req.user_id, shop_id=req.shop_id, product_id=req.product_id).first()
    if not package:
        package = UserPackage(user_id=req.user_id, shop_id=req.shop_id, product_id=req.product_id, balance=0)
        db.session.add(package)

    package.balance += req.calculated_units
    package.last_updated = datetime.datetime.utcnow()

    # Decrement Stock
    if req.product.track_stock:
        req.product.stock_quantity -= req.calculated_units

    db.session.commit()
    flash(f"Payment confirmed. Added {req.calculated_units} units to user.")
    return redirect(url_for('shop.dashboard'))

@bp.route('/reject_payment/<int:request_id>', methods=['POST'])
@login_required
@verify_password_required
def reject_payment(request_id):
    req = SubscriptionRequest.query.get_or_404(request_id)
    if req.shop.owner_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('shop.dashboard'))

    req.status = 'rejected'
    req.processed_at = datetime.datetime.utcnow()
    db.session.commit()
    flash("Payment rejected.")
    return redirect(url_for('shop.dashboard'))

@bp.route('/approve_redemption/<int:req_id>', methods=['POST'])
@login_required
@verify_password_required
def approve_redemption(req_id):
    req = RedemptionRequest.query.get_or_404(req_id)
    if req.shop.owner_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('shop.dashboard'))

    from app.models import UserPackage
    package = UserPackage.query.filter_by(user_id=req.user_id, shop_id=req.shop_id, product_id=req.product_id).first()

    if package and package.balance >= req.units_requested:
        package.balance -= req.units_requested
        req.status = 'approved'
        db.session.commit()
        flash(f"Redemption approved. New balance: {package.balance}")
    else:
        req.status = 'rejected'
        db.session.commit()
        flash("Redemption failed: Insufficient balance.")

    return redirect(url_for('shop.dashboard'))

@bp.route('/reject_redemption/<int:req_id>', methods=['POST'])
@login_required
@verify_password_required
def reject_redemption(req_id):
    req = RedemptionRequest.query.get_or_404(req_id)
    if req.shop.owner_id != current_user.id:
        flash("Unauthorized")
        return redirect(url_for('shop.dashboard'))

    req.status = 'rejected'
    db.session.commit()
    flash("Redemption rejected.")
    return redirect(url_for('shop.dashboard'))
