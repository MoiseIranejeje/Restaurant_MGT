from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'system_admin', 'shop_admin', 'shop_staff', 'buyer'
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=True) # For staff
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shops = db.relationship('Shop', foreign_keys='Shop.owner_id', backref='owner', lazy='dynamic')
    subscription_requests = db.relationship('SubscriptionRequest', backref='buyer', lazy='dynamic')
    packages = db.relationship('UserPackage', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    shop_code = db.Column(db.String(20), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscription_expires_at = db.Column(db.DateTime)
    qr_code_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='shop', lazy='dynamic')
    subscription_requests = db.relationship('SubscriptionRequest', backref='shop', lazy='dynamic')
    staff = db.relationship('User', foreign_keys='User.shop_id', backref='assigned_shop', lazy='dynamic')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_per_unit = db.Column(db.Float, nullable=False)
    unit_name = db.Column(db.String(50), default="Item") # e.g., Plate, Cup, Bowl
    is_active = db.Column(db.Boolean, default=True)

    # Inventory & Discounts
    stock_quantity = db.Column(db.Integer, default=0)
    track_stock = db.Column(db.Boolean, default=False)
    discount_percent = db.Column(db.Integer, default=0)
    discount_end = db.Column(db.DateTime, nullable=True)

class SubscriptionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    calculated_units = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    product = db.relationship('Product')

class UserPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    balance = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    shop = db.relationship('Shop')

class RedemptionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    units_redeemed = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class RedemptionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    units_requested = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
    product = db.relationship('Product')
    shop = db.relationship('Shop')

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
