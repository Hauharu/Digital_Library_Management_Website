from app import bcrypt
from flask_login import login_user as flask_login_user
import re

from app.models import User, RoleEnum
from app.dao.auth_dao import (
    get_user_by_email,
    get_user_by_username,
    create_user,
    commit,
    rollback
)


def register_user(data):
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role_name = data.get("role", "reader").upper()

    if not name:
        return {"error": "Tên không được để trống"}

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"error": "Email không hợp lệ"}

    if len(password) < 6:
        return {"error": "Password >= 6 ký tự"}

    if get_user_by_email(email):
        return {"error": "Email đã tồn tại"}

    try:
        role_enum = RoleEnum[role_name]
    except KeyError:
        return {"error": "Role không tồn tại"}

    try:
        parts = name.split(" ", 1)
        first_name = parts[-1]
        last_name = parts[0] if len(parts) > 1 else ""
        username = data.get("username") or email.split("@")[0]

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
            role=role_enum,
            phone_number=data.get("phone")
        )

        create_user(user)

        commit()

        return {
            "message": "Đăng ký thành công",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": role_enum.value
            }
        }

    except Exception as e:
        rollback()
        return {"error": str(e)}


def login_user_logic(data):
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return {"error": "Username và password không được để trống"}

    user = get_user_by_username(username)
    if not user:
        user = get_user_by_email(username)

    if user and bcrypt.check_password_hash(user.password, password):
        if not user.is_active:
            return {"error": "Tài khoản của bạn đã bị khóa"}

        flask_login_user(user)
        return {
            "message": "Đăng nhập thành công",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role.value
            }
        }

    return {"error": "Username hoặc password không chính xác"}


def logout_user():
    from flask_login import logout_user as flask_logout_user
    flask_logout_user()
    return {"message": "Đăng xuất thành công"}