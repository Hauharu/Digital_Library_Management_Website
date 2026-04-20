from flask import Blueprint, render_template, request, abort
from app import db
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import (
    RoleEnum, User, Book, BorrowRequest,
    BorrowSlip, RequestStatusEnum, BorrowStatusEnum, Category
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_books = Book.query.limit(8).all()
    related_books = Book.query.order_by(db.func.random()).limit(10).all()
    return render_template('index.html', featured_books=featured_books, related_books=related_books)


@main_bp.route('/books')
def book_list():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    per_page = 8
    
    query = Book.query
    category = None
    if category_id:
        category = Category.query.get(category_id)
        query = query.filter_by(category_id=category_id)
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    return render_template('book/book_list.html', books=books, pagination=pagination, category=category)


@main_bp.route('/categories')
def categories():
    categories_list = Category.query.all()
    return render_template('book/categories.html', categories=categories_list)


@main_bp.route('/admin')
@login_required
@role_required(RoleEnum.ADMIN)
def admin_dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_books': Book.query.count(),
        'pending_requests': BorrowRequest.query.filter_by(status='pending').count()
    }
    return render_template('admin/dashboard.html', stats=stats)


@main_bp.route('/book-detail/<int:book_id>')
def book_detail(book_id):
    source = request.args.get('from', 'list')
    book = Book.query.get_or_404(book_id)
    
    if not hasattr(book, 'quantity'):
        setattr(book, 'quantity', book.available_quantity)
    if not hasattr(book, 'book_id'):
        setattr(book, 'book_id', book.id)
            
    related_books = Book.query.filter(Book.id != book.id).all()
    
    user_state = {
        'is_borrowing': False,
        'request_status': None
    }
    
    if current_user.is_authenticated:
        active_slip = BorrowSlip.query.filter_by(
            user_id=current_user.id,
            book_id=book.id,
            status=BorrowStatusEnum.Borrowing
        ).first()

        if active_slip:
            user_state['is_borrowing'] = True
        else:
            active_request = BorrowRequest.query.filter_by(
                user_id=current_user.id,
                book_id=book.id
            ).filter(
                BorrowRequest.status.in_([
                    RequestStatusEnum.Pending,
                    RequestStatusEnum.Approved
                ])
            ).first()

            if active_request:
                user_state['request_status'] = (
                    'pending' if active_request.status == RequestStatusEnum.Pending else 'approved'
                )
            
    return render_template(
        'book/book_detail.html',
        book=book,
        related_books=related_books,
        user_state=user_state,
        source=source
    )


@main_bp.route('/staff')
@login_required
@role_required(RoleEnum.STAFF)
def staff_dashboard():
    pending_list = BorrowRequest.query.filter_by(status='pending').all()
    return render_template('staff/dashboard.html', requests=pending_list)


@main_bp.route('/request-borrow/<int:book_id>', methods=['POST'])
def request_borrow(book_id):
    # Placeholder cho logic mượn sách
    return f"Yêu cầu mượn sách ID {book_id} đã được gửi (Tính năng đang phát triển)"