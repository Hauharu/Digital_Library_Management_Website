from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import User, RequestStatusEnum, BorrowStatusEnum

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route("/profile")
@login_required
def user_profile():
    user = current_user 

    # Đếm số yêu cầu đang chờ hoặc đã duyệt
    active_requests = sum(1 for r in user.borrow_requests if r.status in (RequestStatusEnum.Pending, RequestStatusEnum.Approved))
    
    # Đếm số sách đang mượn từ borrow_slips
    borrow_count = sum(1 for s in user.borrow_slips if s.status == BorrowStatusEnum.Borrowing)

    # Mapping cho view
    user_data = {
        "id": user.id,
        "username": user.username,
        "name": f"{user.last_name} {user.first_name}",
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
    # Hàm cập nhật thông tin người dùng
    pass

@user_bp.route("/profile/password", methods=["POST"])
@login_required
def update_password():
    # Hàm cập nhật mật khẩu
    pass
