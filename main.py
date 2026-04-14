from app import app, db
from app.models import Category, Product

if __name__ == '__main__':
    with app.app_context():
        # c1 = Category(name='Mobile')
        # c2 = Category(name='Tablet')
        # c3 = Category(name='Desktop')
        #
        # db.session.add_all([c1, c2, c3])
        # db.session.commit()
        #
        # p1 = Product(name='iPhone 15', price=20000000, category_id=1)
        # p2 = Product(name='iPad Pro', price=30000000, category_id=2)
        # p3 = Product(name='Galaxy S24', price=25000000, category_id=1)
        # p4 = Product(name='Dell XPS', price=40000000, category_id=3)
        #
        # db.session.add_all([p1, p2, p3, p4])
        # db.session.commit()

        db.create_all()
    app.run(debug=True)

