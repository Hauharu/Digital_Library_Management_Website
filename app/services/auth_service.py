from app import bcrypt
from flask_login import login_user as flask_login_user
import re
from app import db
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
    username = data.get("username", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "").strip()
    role_name = data.get("role", "reader").upper()

    if not all([name, email, username, password]):
        return {"error": "Vui lòng điền đầy đủ các thông tin bắt buộc!"}

    if User.query.filter_by(email=email).first():
        return {"error": "Email này đã được sử dụng bởi một tài khoản khác!"}

    if User.query.filter_by(username=username).first():
        return {"error": "Tên đăng nhập này đã tồn tại!"}

    if phone and User.query.filter_by(phone_number=phone).first():
        return {"error": "Số điện thoại này đã được đăng ký tài khoản khác!"}

    try:
        role_enum = RoleEnum[role_name]

        parts = name.split(" ", 1)
        last_name = parts[0]
        first_name = parts[1] if len(parts) > 1 else ""

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone_number=phone,
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
            role=role_enum,
            avatar='https://res.cloudinary.com/dwwfgtxv4/image/upload/v1776585521/AnhDaiDien_nvnfre.png'
        )

        db.session.add(user)
        db.session.commit()

        return {"message": "Chúc mừng! Bạn đã đăng ký thành công tài khoản OU BOOK."}

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi hệ thống: {str(e)}")
        return {"error": "Đã có lỗi xảy ra trong quá trình lưu dữ liệu. Vui lòng thử lại!"}

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