from werkzeug.security import generate_password_hash
import re

from app.models import User, ReaderProfile, StaffProfile
from app.dao.auth_dao import (
    get_user_by_email,
    get_role_by_name,
    create_user,
    commit,
    rollback
)


def register_user(data):
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role_name = data.get("role", "reader").lower()

    if not name:
        return {"error": "Tên không được để trống"}

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"error": "Email không hợp lệ"}

    if len(password) < 6:
        return {"error": "Password >= 6 ký tự"}

    if get_user_by_email(email):
        return {"error": "Email đã tồn tại"}

    role = get_role_by_name(role_name)
    if not role:
        return {"error": "Role không tồn tại"}

    try:

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role_id=role.id
        )

        create_user(user)

        if role.name == "reader":
            profile = ReaderProfile(
                user_id=user.id,
                phone=data.get("phone"),
                address=data.get("address")
            )

        elif role.name == "staff":
            profile = StaffProfile(
                user_id=user.id,
                salary=data.get("salary", 0),
                position=data.get("position", "Nhân viên")
            )

        else:
            profile = None

        if profile:
            from app.models import db
            db.session.add(profile)

        commit()

        return {
            "message": "Đăng ký thành công",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": role.name
            }
        }

    except Exception as e:
        rollback()
        return {"error": str(e)}