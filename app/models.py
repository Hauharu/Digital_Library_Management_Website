from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db
from flask_login import UserMixin

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    users = db.relationship('User', backref='role', lazy=True)


class User(db.Model,UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reader_profile = db.relationship('ReaderProfile', backref='user', uselist=False)
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False)

    reviews = db.relationship('Review', backref='user', lazy=True)

    borrowed_requests = db.relationship(
        'BorrowRequest',
        foreign_keys='BorrowRequest.user_id',
        backref='reader',
        lazy=True
    )

    processed_requests = db.relationship(
        'BorrowRequest',
        foreign_keys='BorrowRequest.staff_id',
        backref='staff',
        lazy=True
    )

class ReaderProfile(db.Model):
    __tablename__ = 'reader_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)

    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))

    created_at = db.Column(db.DateTime, default=datetime.now)


class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)

    salary = db.Column(db.Integer)
    position = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.now)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    books = db.relationship('Book', backref='category', lazy=True)


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255))

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    reviews = db.relationship('Review', backref='book', lazy=True)


class BorrowRequest(db.Model):
    __tablename__ = 'borrow_requests'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    status = db.Column(db.String(50), default='pending')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)

    details = db.relationship('BorrowDetail', backref='request', lazy=True)


class BorrowDetail(db.Model):
    __tablename__ = 'borrow_details'

    id = db.Column(db.Integer, primary_key=True)

    request_id = db.Column(db.Integer, db.ForeignKey('borrow_requests.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    quantity = db.Column(db.Integer, default=1)

    book = db.relationship('Book')


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.now)


class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))

    action = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User')
    book = db.relationship('Book')


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    user = db.relationship('User')
    category = db.relationship('Category')