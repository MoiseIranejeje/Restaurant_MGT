import unittest
from app import create_app, db
from app.models import User, Shop, Product, SubscriptionRequest, UserPackage
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan', email='susan@example.com', role='buyer')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_shop_creation(self):
        u = User(username='admin', email='admin@example.com', role='shop_admin')
        db.session.add(u)
        db.session.commit()

        shop = Shop(name="Test Shop", owner=u, shop_code="TEST1234")
        db.session.add(shop)
        db.session.commit()

        self.assertEqual(Shop.query.count(), 1)
        self.assertEqual(shop.owner.username, 'admin')

    def test_subscription_flow(self):
        # Create users
        shop_owner = User(username='shop_owner', email='shop@example.com', role='shop_admin')
        buyer = User(username='buyer', email='buyer@example.com', role='buyer')
        db.session.add_all([shop_owner, buyer])
        db.session.commit()

        # Create shop and product
        shop = Shop(name="Pizza Place", owner=shop_owner, shop_code="PIZZA1")
        db.session.add(shop)
        db.session.commit()

        product = Product(shop_id=shop.id, name="Slice", price_per_unit=5.0)
        db.session.add(product)
        db.session.commit()

        # Buyer requests subscription (Pays 50, so 10 slices)
        req = SubscriptionRequest(user_id=buyer.id, shop_id=shop.id, product_id=product.id, amount_paid=50.0, calculated_units=10)
        db.session.add(req)
        db.session.commit()

        self.assertEqual(req.status, 'pending')

        # Shop confirms
        req.status = 'approved'
        pkg = UserPackage(user_id=buyer.id, shop_id=shop.id, product_id=product.id, balance=req.calculated_units)
        db.session.add(pkg)
        db.session.commit()

        self.assertEqual(UserPackage.query.filter_by(user_id=buyer.id).first().balance, 10)

if __name__ == '__main__':
    unittest.main(verbosity=2)
