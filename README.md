# Subscription Commerce Platform

A secure, web-based subscription commerce platform that allows physical shops and restaurants to sell products or food packages through manual payment confirmation and subscription-based packages.

## Features

- **System Owner:** Manage shops and platform settings.
- **Shop Owner:** Manage products, prices, and confirm customer payments/redemptions.
- **Buyer:** Subscribe to products, pay via manual methods (MoMo/Cash), and redeem packages via QR/Code.
- **Tech Stack:** Flask, SQLAlchemy, Tailwind CSS.

## Setup & Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Initialize Database & Seed Data:**
    You can run the application, which will auto-create the DB if configured, or use a seed script.

    *Example Seed Command:*
    ```bash
    python3 -c "from app import create_app, db; from app.models import User, Shop, Product; app = create_app(); app.app_context().push(); db.create_all();
    admin = User(username='sysadmin', email='admin@test.com', role='system_admin'); admin.set_password('password'); db.session.add(admin);
    shop_owner = User(username='shopowner', email='shop@test.com', role='shop_admin'); shop_owner.set_password('password'); db.session.add(shop_owner);
    buyer = User(username='buyer', email='buyer@test.com', role='buyer'); buyer.set_password('password'); db.session.add(buyer);
    shop = Shop(name='Test Shop', owner=shop_owner, shop_code='TEST1', is_active=True); db.session.add(shop);
    product = Product(shop_id=1, name='Test Burger', price_per_unit=10.0, unit_name='Burger'); db.session.add(product);
    from app.models import UserPackage; pkg = UserPackage(user_id=3, shop_id=1, product_id=1, balance=5); db.session.add(pkg);
    db.session.commit();"
    ```

3.  **Run the App:**
    ```bash
    python3 run.py
    ```
    Access at `http://127.0.0.1:5000/`.

## Test Credentials

For testing the flows, use the following pre-configured accounts (after running the seed command):

| Role | Username | Password |
|------|----------|----------|
| **System Admin** | `sysadmin` | `password` |
| **Shop Owner** | `shopowner` | `password` |
| **Buyer** | `buyer` | `password` |

## Project Structure

- `app/` - Application source code.
- `app/templates/` - Jinja2 templates styled with Tailwind CSS.
- `app/routes/` - Blueprint route definitions.
- `app/models.py` - Database models.
