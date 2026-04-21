from flask import Blueprint, render_template, request, abort
from app import db
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import (
    RoleEnum, User, Book, BorrowRequest,
    BorrowSlip, RequestStatusEnum, BorrowStatusEnum, Category
)
from app.services.book_service import BookService
from flask import jsonify
from datetime import datetime
from sqlalchemy import func

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
    total_books = Book.query.count()

    pending_count = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending).count()

    borrowing_count = BorrowSlip.query.filter_by(status=BorrowStatusEnum.Borrowing).count()

    overdue_count = BorrowSlip.query.filter(
        BorrowSlip.due_date < datetime.now().date(),
        BorrowSlip.status == BorrowStatusEnum.Borrowing
    ).count()

    now = datetime.now().strftime('%H:%M - %d/%m/%Y')

    recent_requests = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending) \
        .order_by(BorrowRequest.created_at.desc()).limit(5).all()

    low_stock_books = Book.query.filter(Book.available_quantity < 3).limit(5).all()

    top_books = db.session.query(Book.title, func.count(BorrowSlip.id).label('total')) \
        .join(BorrowSlip, Book.id == BorrowSlip.book_id) \
        .group_by(Book.id).order_by(func.count(BorrowSlip.id).desc()).limit(5).all()

    return render_template('staff/dashboard.html',
                           total_books=total_books,
                           pending_count=pending_count,
                           borrowing_count=borrowing_count,
                           overdue_count=overdue_count,
                           requests=recent_requests,
                           current_time=now,
                           low_stock_books=low_stock_books,
                           top_books=top_books,
                           now=datetime.now())


@main_bp.route('/request-borrow/<int:book_id>', methods=['POST'])
def request_borrow(book_id):
    # Placeholder cho logic mượn sách
    return f"Yêu cầu mượn sách ID {book_id} đã được gửi (Tính năng đang phát triển)"

@main_bp.route("/search")
def search():
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    language = request.args.get('language', '')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    filters = {}
    if category: filters['category'] = int(category) if category.isdigit() else category
    if language: filters['language'] = language
    
    service = BookService()
    
    if not search_query and not filters:
        pagination = service.get_paginated_books(page=page, per_page=per_page, order_desc=True)
    else:
        pagination = service.search_books(keyword=search_query, filters=filters, page=page, per_page=per_page)
    
    filter_options = service.get_filter_options()
    
    return render_template("book/search_results.html", 
                         search_query=search_query, 
                         pagination=pagination, 
                         books=pagination.items if pagination else [],
                         filters=filters,
                         filter_options=filter_options)


@main_bp.route("/search/quick")
def search_quick():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return ""
    service = BookService()
    pagination = service.search_books(keyword=keyword, page=1, per_page=5)
    books = pagination.items if pagination else []
    return render_template("book/partials/quick_search_items.html", books=books)


@main_bp.route('/history')
@login_required
def borrow_history():

    history = BorrowRequest.query.filter_by(user_id=current_user.id) \
        .order_by(BorrowRequest.created_at.desc()).all()

    return render_template('user/history.html', history=history)