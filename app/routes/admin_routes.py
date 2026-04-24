from sqlalchemy import func
from datetime import datetime
from app import db
from app.models import User, Book, Category, BorrowSlip, BorrowRequest, Invoice, RoleEnum, RequestStatusEnum, BorrowStatusEnum
from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from flask_login import login_required
from app.decorators import role_required
import cloudinary.uploader

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