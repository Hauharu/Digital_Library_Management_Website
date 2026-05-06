from functools import wraps
from flask_login import current_user
from flask import abort


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401)
            
            # Lấy danh sách tên các quyền được phép (ví dụ: ['ADMIN', 'STAFF'])
            allowed_roles = [r.name if hasattr(r, 'name') else str(r) for r in roles]
            
            if current_user.role.name not in allowed_roles:
                return abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator