from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, logout_user
from app.models import User, RequestStatusEnum, BorrowStatusEnum, GenderEnum,Book
from app import db, bcrypt
from datetime import datetime
from app.services.borrow_service import BorrowService

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


@user_bp.route("/notifications")
@login_required
def notifications():
    from app.models import Notification
    all_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.sent_date.desc()).all()
    
    selected_id = request.args.get('id', type=int)
    selected_notif = None
    if selected_id:
        selected_notif = Notification.query.get(selected_id)
        if selected_notif and selected_notif.user_id == current_user.id:
            if not selected_notif.is_read:
                selected_notif.is_read = True
                db.session.commit()
    elif all_notifications:
        selected_notif = all_notifications[0]
        if not selected_notif.is_read:
            selected_notif.is_read = True
            db.session.commit()
            
    return render_template("user/notifications.html", 
                           all_notifications=all_notifications, 
                           selected_notif=selected_notif)

@user_bp.route("/notifications/delete/<int:notif_id>", methods=["POST"])
@login_required
def delete_notification(notif_id):
    from app.models import Notification
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Không có quyền'}), 403
    
    db.session.delete(notif)
    db.session.commit()
    return jsonify({'success': True})

@user_bp.route("/notifications/delete-all", methods=["POST"])
@login_required
def delete_all_notifications():
    from app.models import Notification
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})

@user_bp.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    quantity_available = book.available_quantity or 0

    if request.method == 'POST':
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        quantity_str = request.form.get('quantity', '1').strip()

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Ngày mượn hoặc ngày trả không hợp lệ.', 'danger')
            return redirect(url_for('borrow_book', book_id=book_id))

        try:
            quantity = int(quantity_str)
        except ValueError:
            flash('Số lượng mượn phải là số nguyên.', 'danger')
            return redirect(url_for('borrow_book', book_id=book_id))

        result = BorrowService.create_borrow_request(
            user=current_user,
            book=book,
            start_date=start_date,
            end_date=end_date,
            quantity=quantity
        )

        flash(result['message'], result['category'])
        if result['ok']:
            return redirect(url_for('main.book_detail', book_id=book_id, **{'from': 'featured'}))

        return redirect(url_for('borrow_book', book_id=book_id))

    return render_template(
        'book/borrow_form.html',
        user=current_user,
        book=book,
        quantity_available=quantity_available,
        today=datetime.now().date().isoformat()
    )