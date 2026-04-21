from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from app.models import User, RequestStatusEnum, BorrowStatusEnum, GenderEnum
from app import db, bcrypt

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route("/profile")
@login_required
def user_profile():
    user = current_user 

    # Đếm số yêu cầu đang chờ hoặc đã duyệt
    active_requests = sum(1 for r in user.borrow_requests if r.status in (RequestStatusEnum.Pending, RequestStatusEnum.Approved))
    
    # Đếm số sách đang mượn từ borrow_slips
    borrow_count = sum(1 for s in user.borrow_slips if s.status == BorrowStatusEnum.Borrowing)

    full_name = " ".join([part.strip() for part in [user.last_name or "", user.first_name or ""] if part and part.strip()])
    display_name = full_name or user.username or user.email

    # Mapping cho view
    user_data = {
        "id": user.id,
        "username": user.username,
        "name": display_name,
        "borrow_count": borrow_count,
        "pending_books": active_requests,
        "email": user.email,
        "phone_number": user.phone_number or "",
        "gender": "Nam" if user.gender and user.gender.name == "MALE" else ("Nữ" if user.gender and user.gender.name == "FEMALE" else "Khác")
    }
    
    return render_template("user/user_profile.html", user_info=user_data)


@user_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    gender_str = request.form.get('gender')

    if full_name:
        name_parts = full_name.split()
        if len(name_parts) > 1:
            current_user.first_name = name_parts[-1]
            current_user.last_name = " ".join(name_parts[:-1])
        else:
            current_user.first_name = name_parts[0]
            current_user.last_name = ""

    current_user.phone_number = phone_number
    
    if gender_str == "Nam":
        current_user.gender = GenderEnum.MALE
    elif gender_str == "Nữ":
        current_user.gender = GenderEnum.FEMALE
    else:
        current_user.gender = GenderEnum.OTHER

    db.session.commit()
    flash("Cập nhật thông tin thành công!", "success")
    return redirect(url_for('user.user_profile'))


@user_bp.route("/profile/password", methods=["POST"])
@login_required
def update_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not bcrypt.check_password_hash(current_user.password, current_password):
        flash("Mật khẩu hiện tại không chính xác!", "danger")
        return redirect(url_for('user.user_profile'))

    if new_password != confirm_password:
        flash("Mật khẩu mới không khớp!", "danger")
        return redirect(url_for('user.user_profile'))

    current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    
    logout_user() # Đăng xuất người dùng
    flash("Đổi mật khẩu thành công! Vui lòng đăng nhập lại.", "success")
    return redirect(url_for('auth.login'))
