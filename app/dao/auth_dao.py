from app.models import db, User


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def create_user(user):
    db.session.add(user)
    db.session.flush()

def commit():
    db.session.commit()


def rollback():
    db.session.rollback()
