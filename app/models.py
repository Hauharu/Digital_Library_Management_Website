from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    users = db.relationship('User', backref='role', lazy=True)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)

    borrow_requests = db.relationship('BorrowRequest', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    books = db.relationship('Book', backref='category', lazy=True)


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20))
    publication_info = db.Column(db.String(255))
    language = db.Column(db.String(50))
    title = db.Column(db.String(255))
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    reviews = db.relationship('Review', backref='book', lazy=True)


class BorrowRequest(db.Model):
    __tablename__ = 'borrow_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    details = db.relationship('BorrowDetail', backref='request', lazy=True)


class BorrowDetail(db.Model):
    __tablename__ = 'borrow_details'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('borrow_requests.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    quantity = db.Column(db.Integer)

    book = db.relationship('Book')


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)


class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    book_id = db.Column(db.Integer)

    action = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
