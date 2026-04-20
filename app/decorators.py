from functools import wraps
from flask_login import current_user
from flask import abort


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401)
            if current_user.role != role:
                return abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator