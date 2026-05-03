from sqlalchemy import func, extract, cast, Date
from datetime import datetime, timedelta
from app import db
from app.models import User, Book, Category, BorrowSlip, BorrowRequest, Invoice, RoleEnum,\
    RequestStatusEnum, BorrowStatusEnum, GenderEnum, Payment,PaymentMethodEnum,PaymentStatusEnum, db
from flask import Blueprint, render_template, request, abort, redirect, url_for, flash,jsonify
from flask_login import login_required,current_user
from app.decorators import role_required
import cloudinary.uploader
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required(RoleEnum.ADMIN)
def admin_dashboard():
    total_users = User.query.count()
    total_revenue = db.session.query(func.sum(Invoice.amount)).scalar() or 0
    total_books = Book.query.count()
    active_borrows = BorrowSlip.query.filter_by(status=BorrowStatusEnum.Borrowing).count()
    pending_requests = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending).order_by(BorrowRequest.created_at.desc()).limit(8).all()
    pending_return_requests = BorrowSlip.query.filter_by(
        status=BorrowStatusEnum.Borrowing,
        return_requested=True
    ).order_by(BorrowSlip.updated_at.desc()).limit(8).all()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    current_year = datetime.now().year
    revenue_by_month = [0.0] * 12

    try:
        monthly_revenue_query = db.session.query(
            func.extract('month', Invoice.created_at).label('month'),
            func.sum(Invoice.amount).label('total')
        ).filter(func.extract('year', Invoice.created_at) == current_year) \
            .group_by('month').all()

        for row in monthly_revenue_query:
            month_idx = int(row.month) - 1
            if 0 <= month_idx < 12:
                revenue_by_month[month_idx] = float(row.total or 0)
    except Exception as e:
        print(f"Lỗi truy vấn doanh thu: {e}")
        revenue_by_month = [0.0] * 12

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_revenue=total_revenue,
                           total_books=total_books,
                           active_borrows=active_borrows,
                           pending_requests=pending_requests,
                           pending_return_requests=pending_return_requests,
                           recent_users=recent_users,
                           revenue_data=revenue_by_month,
                           now=datetime.now())

@admin_bp.route('/add-book', methods=['GET', 'POST'])
@login_required
@role_required(RoleEnum.ADMIN)
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        isbn = request.form.get('isbn')
        author = request.form.get('author')
        category_id = request.form.get('category_id')
        price = request.form.get('price', 0)
        language = request.form.get('language')
        total_quantity = request.form.get('total_quantity', 0)
        publication_info = request.form.get('publication_info')
        description = request.form.get('description')
        
        image_file = request.files.get('image')
        image_url = None
        
        if image_file:
            try:
                upload_result = cloudinary.uploader.upload(image_file)
                image_url = upload_result.get('secure_url')
            except Exception as e:
                flash(f"Lỗi khi tải ảnh lên Cloudinary: {str(e)}", "warning")

        new_book = Book(
            title=title,
            isbn=isbn,
            author=author,
            category_id=category_id,
            price=float(price) if price else 0.0,
            language=language,
            total_quantity=int(total_quantity) if total_quantity else 0,
            available_quantity=int(total_quantity) if total_quantity else 0,
            publication_info=publication_info,
            description=description,
            image=image_url
        )
        
        try:
            db.session.add(new_book)
            db.session.commit()
            flash("Thêm sách mới thành công!", "success")
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi thêm sách vào cơ sở dữ liệu: {str(e)}", "danger")

    categories = Category.query.all()
    return render_template('admin/add_book.html', categories=categories)

@admin_bp.route('/books')
@login_required
@role_required(RoleEnum.ADMIN)
def manage_books():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Book.query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    return render_template('admin/manage_books.html', books=books, pagination=pagination)


@admin_bp.route('/users')
@login_required
@role_required(RoleEnum.ADMIN)
def manage_users():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    reader_pagination = User.query.filter_by(role=RoleEnum.READER) \
        .order_by(User.id.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    staff_list = User.query.filter_by(role=RoleEnum.STAFF).all()

    return render_template('admin/manage_users.html',
                           staff_list=staff_list,
                           reader_pagination=reader_pagination,
                           readers=reader_pagination.items)

@admin_bp.route('/api/user/<int:user_id>')
@login_required
@role_required(RoleEnum.ADMIN)
def get_user_api(user_id):
    u = User.query.get_or_404(user_id)
    return jsonify({
        "id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "username": u.username,
        "email": u.email,
        "phone_number": u.phone_number,
        "gender": u.gender.value if u.gender else "OTHER",
        "role": u.role.value if u.role else "READER",
        "is_active": u.is_active,
        "avatar": u.avatar
    })


@admin_bp.route('/users/add', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN)
def add_user():
    try:
        data = request.form
        phone = data.get('phone_number')
        if not phone or phone.strip() == "":
            phone = None

        if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
            flash("Username hoặc Email đã tồn tại!", "danger")
            return redirect(url_for('admin.manage_users'))

        new_user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            username=data['username'],
            email=data['email'],
            phone_number=phone,
            gender=GenderEnum(data['gender']),
            role=RoleEnum(data['role']),
            password=generate_password_hash("123456")
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Thêm người dùng mới thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi: {str(e)}", "danger")

    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.ADMIN)
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Bạn không thể tự xóa chính mình!", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"Đã xóa tài khoản {user.username} thành công!", "success")

    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/revenue_report')
@login_required
@role_required(RoleEnum.ADMIN)
def revenue_report():

    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', type=int)

    base_query = Payment.query.filter(Payment.status == PaymentStatusEnum.Completed)

    if month:
        base_query = base_query.filter(extract('month', Payment.payment_date) == month)
    if year:
        base_query = base_query.filter(extract('year', Payment.payment_date) == year)

    payments = base_query.order_by(Payment.payment_date.desc()).all()
    total_revenue = sum(p.amount_paid for p in payments)
    avg_payment = total_revenue / len(payments) if payments else 0

    if month:
        chart_data = db.session.query(
            func.date(Payment.payment_date).label('date'),
            func.sum(Payment.amount_paid).label('total')
        ).filter(Payment.status == PaymentStatusEnum.Completed,
                 extract('month', Payment.payment_date) == month,
                 extract('year', Payment.payment_date) == year) \
            .group_by(func.date(Payment.payment_date)).all()
    else:
        chart_data = db.session.query(
            extract('month', Payment.payment_date).label('date'),
            func.sum(Payment.amount_paid).label('total')
        ).filter(Payment.status == PaymentStatusEnum.Completed,
                 extract('year', Payment.payment_date) == year) \
            .group_by(extract('month', Payment.payment_date)).all()

    top_books = db.session.query(
        Book.title,
        func.sum(Payment.amount_paid).label('revenue')
    ).join(BorrowSlip, Book.id == BorrowSlip.book_id) \
        .join(Invoice, BorrowSlip.id == Invoice.borrow_slip_id) \
        .join(Payment, Invoice.id == Payment.invoice_id) \
        .filter(Payment.status == PaymentStatusEnum.Completed) \
        .group_by(Book.title).order_by(func.sum(Payment.amount_paid).desc()).limit(5).all()

    return render_template('admin/revenue_report.html',
                           payments=payments,
                           datetime=datetime,
                           total_revenue=total_revenue,
                           avg_payment=avg_payment,
                           chart_data=chart_data,
                           top_books=top_books,
                           current_year=year,
                           current_month=month)