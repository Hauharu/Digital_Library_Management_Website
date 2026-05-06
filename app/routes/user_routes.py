from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, logout_user
from app.services.borrow_service import BorrowService
from app.services.email_service import EmailService
from app.services.payment_service import PaymentService
from app.models import User, RequestStatusEnum, BorrowStatusEnum, GenderEnum, Book, Invoice, Payment, PaymentMethodEnum, InvoiceStatusEnum, RoleEnum
from app import db, bcrypt
from datetime import datetime, date
from app.decorators import role_required
user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route("/profile")
@login_required
@role_required(RoleEnum.READER)
def user_profile():
    user = current_user 

    # Đếm số yêu cầu đang chờ xử lý
    active_requests = sum(1 for r in user.borrow_requests if r.status == RequestStatusEnum.Pending)
    
    # Đếm số sách đang nắm giữ hoặc chịu trách nhiệm (chưa trả)
    borrow_count = sum(1 for s in user.borrow_slips if s.status != BorrowStatusEnum.Returned)

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
        "gender": "Nam" if user.gender and user.gender.name == "MALE" else ("Nữ" if user.gender and user.gender.name == "FEMALE" else "Khác"),
        "avatar": user.avatar
    }
    
    return render_template("user/user_profile.html", user_info=user_data)


@user_bp.route("/profile/update", methods=["POST"])
@login_required
@role_required(RoleEnum.READER)
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
@role_required(RoleEnum.READER)
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

    EmailService.send_general_notification(
        current_user.first_name,
        current_user.email,
        "Mật khẩu tài khoản đã được thay đổi",
        "Chúng tôi thông báo rằng mật khẩu của bạn tại OU BOOK vừa được cập nhật thành công qua trang cá nhân.")
    
    logout_user() # Đăng xuất người dùng
    flash("Đổi mật khẩu thành công! Vui lòng đăng nhập lại.", "success")
    return redirect(url_for('auth.login'))


@user_bp.route("/notifications")
@login_required
@role_required(RoleEnum.READER, RoleEnum.STAFF, RoleEnum.ADMIN)
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
@role_required(RoleEnum.READER, RoleEnum.STAFF, RoleEnum.ADMIN)
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
@role_required(RoleEnum.READER, RoleEnum.STAFF, RoleEnum.ADMIN)
def delete_all_notifications():
    from app.models import Notification
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})

@user_bp.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
@login_required
@role_required(RoleEnum.READER)
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
            EmailService.send_general_notification(
                current_user.first_name,
                current_user.email,
                f"Xác nhận yêu cầu mượn sách: {book.title}",
                f"Yêu cầu mượn cuốn sách <b>{book.title}</b> của bạn đã được gửi đến thủ thư. Vui lòng chờ thông báo duyệt từ hệ thống."
            )
            return redirect(url_for('main.book_detail', book_id=book_id, **{'from': 'featured'}))

        return redirect(url_for('borrow_book', book_id=book_id))

    return render_template(
        'book/borrow_form.html',
        user=current_user,
        book=book,
        quantity_available=quantity_available,
        today=datetime.now().date().isoformat()
    )

# ================= PAYMENT ROUTES =================

@user_bp.route("/payment/select/<int:invoice_id>")
@login_required
@role_required(RoleEnum.READER)
def select_payment_method(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    if invoice.borrow_slip.user_id != current_user.id:
        flash("Bạn không có quyền truy cập hóa đơn này.", "danger")
        return redirect(url_for('main.borrow_history'))
    
    if invoice.status == InvoiceStatusEnum.Paid:
        flash("Hóa đơn này đã được thanh toán.", "info")
        return redirect(url_for('main.borrow_history'))

    PaymentService.sync_invoice_amount(invoice)

    return render_template("user/payment_select.html", invoice=invoice)

@user_bp.route("/payment/vnpay/<int:invoice_id>")
@login_required
@role_required(RoleEnum.READER)
def process_vnpay(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    PaymentService.sync_invoice_amount(invoice)
    
    ip_address = request.remote_addr
    payment_url = PaymentService.generate_vnpay_url(invoice.id, invoice.amount, ip_address)
    return redirect(payment_url)

@user_bp.route("/payment/vnpay-return")
def vnpay_return():
    data = request.args.to_dict()
    success, message = PaymentService.process_vnpay_result(data)
    if success:
        # flash(message, "success")
        pass
    else:
        flash(message, "danger")
    return redirect(url_for('main.borrow_history'))

@user_bp.route("/payment/paypal/<int:invoice_id>")
@login_required
def process_paypal(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # Đồng bộ lại giá tiền trước khi thanh toán
    PaymentService.sync_invoice_amount(invoice)
    
    paypal_payment = PaymentService.create_paypal_payment(invoice.id, invoice.amount)
    if paypal_payment:
        for link in paypal_payment['links']:
            if link['rel'] == 'approval_url':
                return redirect(link['href'])
    flash("Có lỗi xảy ra khi khởi tạo PayPal.", "danger")
    return redirect(url_for('user.select_payment_method', invoice_id=invoice_id))

@user_bp.route("/payment/paypal-return")
@login_required
def paypal_return():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    invoice_id = request.args.get('invoice_id')
    
    success, message = PaymentService.process_paypal_result(payment_id, payer_id, invoice_id)
    if success:
        flash("Thanh toán PayPal thành công!", "success")
    else:
        flash(message, "danger")
        
    return redirect(url_for('main.borrow_history'))

@user_bp.route("/payment/paypal-cancel")
@login_required
def paypal_cancel():
    flash("Bạn đã hủy thanh toán PayPal.", "info")
    return redirect(url_for('main.borrow_history'))

@user_bp.route("/payment/offline/<int:invoice_id>", methods=["POST"])
@login_required
def process_offline(invoice_id):
    success, message = PaymentService.process_offline_payment(invoice_id)
    if success:
        # Đã bỏ thông báo theo yêu cầu
        pass
    else:
        flash(message, "danger")
    return redirect(url_for('main.borrow_history'))
    
@user_bp.route("/profile/avatar", methods=["POST"])
@login_required
def update_avatar():
    import cloudinary.uploader
    if 'avatar' not in request.files:
        flash("Không có tệp nào được chọn!", "warning")
        return redirect(request.referrer or url_for('user.user_profile'))
    
    file = request.files['avatar']
    if file.filename == '':
        flash("Chưa có tệp nào được chọn!", "warning")
        return redirect(request.referrer or url_for('user.user_profile'))
    
    try:
        upload_result = cloudinary.uploader.upload(file, folder="library/avatars")
        current_user.avatar = upload_result.get('secure_url')
        db.session.commit()
        flash("Cập nhật ảnh đại diện thành công!", "success")
    except Exception as e:
        flash(f"Lỗi khi tải ảnh lên: {str(e)}", "danger")
        
    return redirect(request.referrer or url_for('user.user_profile'))
