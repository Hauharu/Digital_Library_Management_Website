from app.models import db, User, Role



def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)


def create_user(user):
    db.session.add(user)
    db.session.flush()


def get_role_by_name(role_name):
    return Role.query.filter_by(name=role_name).first()



def commit():
    db.session.commit()

def rollback():
    db.session.rollback()