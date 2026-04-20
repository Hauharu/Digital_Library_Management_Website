from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import User, RequestStatusEnum, BorrowStatusEnum

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route("/profile")
# @login_required  # Tạm thời tắt để test giao diện
def user_profile():
    # Tạm thời vô hiệu hóa current_user.id và lấy cứng User có id = 3 để test
    user = User.query.get(3) 
    if not user:
        # Nếu chưa có user 3, tạo mock data tạm để render được HTML dựa trên thông tin trong data_library_db.txt
        user_data = {
            "id": 3,
            "username": "user",
            "name": "Normal Reader",
            "borrow_count": 0,
            "pending_books": 0,
            "email": "user@library.com",
            "phone_number": "0901234567",
            "gender": "Nam"
        }
        return render_template("user/user_profile.html", current_user=user_data)


    active_requests = sum(1 for r in user.borrow_requests if r.status in (RequestStatusEnum.Pending, RequestStatusEnum.Approved))
    borrow_count = sum(1 for r in user.borrow_slips if r.status == BorrowStatusEnum.Borrowing)

    # Mapping cho view để dùng đúng biến
    user_data = {
        "id": user.id,
        "username": user.username,
        "name": f"{user.last_name} {user.first_name}".strip(),
        "borrow_count": borrow_count,
        "pending_books": active_requests,
        "email": user.email,
        "phone_number": user.phone_number if user.phone_number else "",
        "gender": user.gender.value if user.gender else ""
    }
    
    return render_template("user/user_profile.html", current_user=user_data)


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
