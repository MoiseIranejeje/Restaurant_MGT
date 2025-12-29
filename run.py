from app import create_app, db
from app.models import User, Shop, Product

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Shop': Shop, 'Product': Product}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
