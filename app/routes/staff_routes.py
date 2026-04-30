from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from app.models import BorrowRequest, RequestStatusEnum, Book, User, RoleEnum,\
        BorrowStatusEnum, BorrowSlip,GenderEnum, Invoice, InvoiceStatusEnum, Payment, \
        PaymentMethodEnum, PaymentStatusEnum, Category
from app.services.staff_service import StaffService
from flask_login import login_required
from sqlalchemy import or_
from datetime import datetime, timedelta
from app import db

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.app_context_processor
def inject_pending_count():
    count = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending).count()
    return dict(pending_count=count)

@staff_bp.route('/orders')
@login_required
def manage_orders():
    active_slips = StaffService.get_active_orders(
        search_query=request.args.get('search', '').strip(),
        status_filter=request.args.get('status', ''),
        date_filter=request.args.get('from_date', '')
    )
    return render_template('staff/staff_orders.html', active_slips=active_slips)

@staff_bp.route('/confirm-return/<int:slip_id>', methods=['POST'])
@login_required
def confirm_return(slip_id):
    book_title = StaffService.process_return(slip_id)
    flash(f"Đã nhận trả sách: {book_title}", "success")
    return redirect(url_for('staff.manage_orders'))

@staff_bp.route('/confirm-payment/<int:invoice_id>', methods=['POST'])
@login_required
def confirm_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = InvoiceStatusEnum.Paid
    
    payment = Payment(
        amount_paid=invoice.amount,
        method=PaymentMethodEnum.Cash,
        status=PaymentStatusEnum.Completed,
        transaction_id=f"STAFF_CONFIRM_{invoice.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        invoice_id=invoice.id,
        notes=f"Thủ thư xác nhận thanh toán tiền mặt tại quầy."
    )
    db.session.add(payment)
    db.session.commit()
    
    flash("Đã xác nhận thanh toán thành công!", "success")
    return redirect(url_for('staff.manage_orders'))

@staff_bp.route('/approve-request/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    success, message = StaffService.process_approve(request_id)
    if success:
        flash(f"Đã duyệt yêu cầu của {message}!", "success")
    else:
        flash(message, "danger")
    return redirect(url_for('staff.staff_requests'))

@staff_bp.route('/reject-request/<int:request_id>', methods=['POST'])
@login_required
def reject_request(request_id):
    reason = request.form.get('reject_reason', 'Không rõ lý do')
    StaffService.process_reject(request_id, reason)
    flash("Đã từ chối yêu cầu.", "info")
    return redirect(url_for('staff.staff_requests'))

@staff_bp.route('/requests')
@login_required
def staff_requests():
    pending_requests = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending).all()
    return render_template('staff/staff_requests.html', pending_requests=pending_requests)


@staff_bp.route('/run-overdue-check')
@login_required
def run_overdue_check():

    count = StaffService.notify_overdue_slips()

    if count > 0:
        flash(f"Thành công! Đã gửi email nhắc nhở cho {count} độc giả quá hạn.", "success")
    else:
        flash("Hiện tại không có độc giả nào quá hạn sách.", "info")

    return redirect(url_for('staff.manage_orders'))


@staff_bp.route('/report-incident/<int:slip_id>', methods=['POST'])
@login_required
def report_incident(slip_id):

    damage_ratio = request.form.get('damage_ratio')
    description = request.form.get('description')
    fine_amount = request.form.get('fine_amount')

    StaffService.report_incident(slip_id, damage_ratio, description, fine_amount)

    flash('Đã ghi nhận sự cố !', 'success')
    return redirect(url_for('staff.manage_orders'))


@staff_bp.route('/incident-report/<int:slip_id>')
@login_required
def incident_report_page(slip_id):
    from app.models import BorrowSlip
    slip = BorrowSlip.query.get_or_404(slip_id)
    return render_template('staff/incident_report.html', slip=slip)


@staff_bp.route('/manage-books')
@login_required
def manage_books():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    cat_id = request.args.get('category_id', 'all')

    pagination = StaffService.get_filtered_books(
        page=page,
        per_page=8,
        search_query=search,
        category_id=cat_id
    )

    categories = StaffService.get_all_categories()
    return render_template('staff/manage_books.html',
                           books=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           search=search,
                           current_cat=cat_id)

@staff_bp.route('/add-book', methods=['POST'])
@login_required
def add_book():
    data = request.form.to_dict()
    image_file = request.files.get('image')
    if StaffService.create_book(data, image_file):
        flash('Thêm sách mới thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi thêm sách.', 'danger')
    return redirect(url_for('staff.manage_books'))

@staff_bp.route('/edit-book/<int:id>', methods=['POST'])
@login_required
def edit_book(id):
    data = request.form.to_dict()
    image_file = request.files.get('image')
    if StaffService.update_book(id, data, image_file):
        flash('Cập nhật thông tin thành công!', 'success')
    return redirect(url_for('staff.manage_books'))

@staff_bp.route('/delete-book/<int:id>', methods=['POST'])
@login_required
def delete_book(id):
    result = StaffService.delete_book(id)
    if result == True:
        flash('Đã xóa sách thành công!', 'success')
    elif result == "cannot_delete_borrowed":
        flash('Không thể xóa vì sách đang có người mượn!', 'warning')
    else:
        flash('Lỗi hệ thống khi xóa sách.', 'danger')
    return redirect(url_for('staff.manage_books'))

@staff_bp.route('/api/book/<int:id>')
def get_book_api(id):
    book = Book.query.get_or_404(id)
    return jsonify({
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "category_id": book.category_id,
        "category_name": book.category.name,
        "isbn": book.isbn,
        "language": book.language,
        "publication_info": book.publication_info,
        "price": book.price,
        "total_quantity": book.total_quantity,
        "available_quantity": book.available_quantity,
        "description": book.description,
        "image": book.image
    })


@staff_bp.route('/create-borrow')
@login_required
def create_borrow():
    books = Book.query.filter(Book.available_quantity > 0).all()
    return render_template('staff/create_borrow.html', books=books)


@staff_bp.route('/api/check-reader')
@login_required
def check_reader():
    try:
        q = request.args.get('phone')
        user = User.query.filter(or_(User.phone_number == q, User.email == q)).first()

        if user:
            return jsonify({
                "exists": True,
                "name": f"{user.last_name} {user.first_name}",
                "id": user.id,
                "email": user.email,
                "phone": user.phone_number
            })
        return jsonify({"exists": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@staff_bp.route('/api/quick-register', methods=['POST'])
@login_required
def api_quick_register():
    data = request.json
    try:
        input_val = data.get('phone')
        full_name = data.get('full_name', '').strip()

        if "@" in input_val:
            final_email = input_val
            final_username = input_val.split('@')[0]
        else:
            final_email = f"{input_val}@library.com"
            final_username = input_val

        name_parts = full_name.split()
        f_name = name_parts[-1] if name_parts else "Reader"
        l_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else "Người dùng"

        new_user = User(
            first_name=f_name,
            last_name=l_name,
            username=final_username,
            email=final_email,
            phone_number=input_val if "@" not in input_val else None,
            password="pbkdf2:sha256:260000$default_password",
            gender=GenderEnum.OTHER,
            role=RoleEnum.READER,
            is_active=True
        )

        db.session.add(new_user)
        db.session.commit()

        try:
            if "@library.com" not in final_email:
                msg = Message(
                    subject="Chào mừng bạn đến với Thư viện số!",
                    recipients=[final_email]
                )
                msg.body = f"""
                        Chào {full_name},

                        Tài khoản thư viện của bạn đã được khởi tạo bởi Thủ thư.

                        Thông tin đăng nhập:
                        - Username: {final_username}
                        - Mật khẩu mặc định: {default_password}

                        Vui lòng đăng nhập và đổi mật khẩu để bảo mật tài khoản.
                        Trân trọng!
                        """
                mail.send(msg)
                print(f"Đã gửi mail thông báo tới {final_email}")
        except Exception as mail_err:
            print(f"Lỗi gửi mail: {mail_err}")

        return jsonify({
            "success": True,
            "id": new_user.id,
            "name": f"{l_name} {f_name}",
            "phone": new_user.phone_number or "N/A",
            "email": new_user.email
        })

    except Exception as e:
        db.session.rollback()
        print(f"LỖI DATABASE: {str(e)}")
        return jsonify({"success": False, "message": "Username hoặc Email đã tồn tại!"}), 500


@staff_bp.route('/api/create-borrow-slip', methods=['POST'])
@login_required
def api_create_borrow_slip():
    data = request.json
    user_id = data.get('user_id')
    items = data.get('items')

    try:
        user = User.query.get(user_id)

        overdue_slips = [s for s in user.borrow_slips if s.status == BorrowStatusEnum.Overdue]
        unpaid_invoices = [i for i in Invoice.query.filter_by(status=InvoiceStatusEnum.Pending).all()
                           if i.borrow_slip.user_id == user_id]

        if overdue_slips or unpaid_invoices:
            return jsonify({
                "success": False,
                "message": "Độc giả đang có sách quá hạn hoặc nợ tiền phạt. Không thể cho mượn!"
            }), 400

        for item in items:
            book = Book.query.get(item['book_id'])
            qty = int(item['quantity'])
            due_days = int(item['due_days'])

            if book.available_quantity < qty:
                return jsonify({"success": False, "message": f"Sách '{book.title}' không đủ số lượng trong kho!"}), 400

            if due_days > 30:
                due_days = 30

            book.available_quantity -= qty

            new_slip = BorrowSlip(
                user_id=user_id,
                book_id=book.id,
                quantity=qty,  
                borrow_date=datetime.now().date(),
                due_date=datetime.now().date() + timedelta(days=due_days),
                status=BorrowStatusEnum.Borrowing
            )
            db.session.add(new_slip)

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@staff_bp.route('/manage-categories')
@login_required
def manage_categories():
    categories = Category.query.all()
    return render_template('staff/manage_categories.html', categories=categories)


@staff_bp.route('/add-category', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Tên thể loại không được để trống!', 'danger')
        return redirect(url_for('staff.manage_categories'))

    existing = Category.query.filter_by(name=name).first()
    if existing:
        flash('Thể loại này đã tồn tại!', 'warning')
        return redirect(url_for('staff.manage_categories'))

    new_cat = Category(name=name)
    db.session.add(new_cat)
    db.session.commit()
    flash(f'Đã thêm thể loại "{name}" thành công!', 'success')
    return redirect(url_for('staff.manage_categories'))


@staff_bp.route('/edit-category/<int:id>', methods=['POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    new_name = request.form.get('name', '').strip()

    if new_name:
        existing = Category.query.filter(Category.name == new_name, Category.id != id).first()
        if existing:
            flash('Tên thể loại đã tồn tại!', 'warning')
        else:
            category.name = new_name
            db.session.commit()
            flash('Cập nhật thể loại thành công!', 'success')

    return redirect(url_for('staff.manage_categories'))


@staff_bp.route('/delete-category/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)

    if category.books:
        flash(f'Không thể xóa vì vẫn còn {len(category.books)} cuốn sách thuộc thể loại này!', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Đã xóa thể loại thành công!', 'success')

    return redirect(url_for('staff.manage_categories'))