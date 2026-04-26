from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from app import db
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import (
    RoleEnum, User, Book, BorrowRequest,
    BorrowSlip, RequestStatusEnum, BorrowStatusEnum, Category, Invoice
)
from app.services.book_service import BookService
from flask import jsonify
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.services.email_service import EmailService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_books = Book.query.order_by(Book.view_count.desc()).limit(10).all()
    related_books = Book.query.order_by(db.func.random()).limit(10).all()
    return render_template('index.html', featured_books=featured_books, related_books=related_books)


@main_bp.route('/books')
def book_list():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    per_page = 10
    
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
def admin_redirect():
    return redirect(url_for('admin.admin_dashboard'))

@main_bp.route('/book-detail/<int:book_id>')
def book_detail(book_id):
    source = request.args.get('from', 'list')
    book = Book.query.get_or_404(book_id)
    
    if not hasattr(book, 'quantity'):
        setattr(book, 'quantity', book.available_quantity)
    if not hasattr(book, 'book_id'):
        setattr(book, 'book_id', book.id)
            
    # Tăng lượt xem thực tế
    if not book.view_count:
        book.view_count = 0
    book.view_count += 1
    db.session.commit()
            
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
            
    from app.models import Review
    discussions = Review.query.filter_by(book_id=book.id).order_by(Review.created_at.asc()).all()

    
    return render_template(
        'book/book_detail.html',
        book=book,
        related_books=related_books,
        user_state=user_state,
        source=source,
        discussions=discussions
    )


@main_bp.route('/staff')
@login_required
@role_required(RoleEnum.STAFF)
def staff_dashboard():
    total_books = Book.query.count()

    pending_count = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending).count()
    return_pending_count = BorrowSlip.query.filter_by(
        status=BorrowStatusEnum.Borrowing,
        return_requested=True
    ).count()

    borrowing_count = BorrowSlip.query.filter_by(status=BorrowStatusEnum.Borrowing).count()

    overdue_count = BorrowSlip.query.filter(
        BorrowSlip.due_date < datetime.now().date(),
        BorrowSlip.status == BorrowStatusEnum.Borrowing
    ).count()

    now = datetime.now().strftime('%H:%M - %d/%m/%Y')

    recent_requests = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending) \
        .order_by(BorrowRequest.created_at.desc()).limit(5).all()
    return_requests = BorrowSlip.query.filter_by(
        status=BorrowStatusEnum.Borrowing,
        return_requested=True
    ).order_by(BorrowSlip.updated_at.desc()).limit(5).all()

    low_stock_books = Book.query.filter(Book.available_quantity < 3).limit(5).all()

    top_books = db.session.query(Book.title, func.count(BorrowSlip.id).label('total')) \
        .join(BorrowSlip, Book.id == BorrowSlip.book_id) \
        .group_by(Book.id).order_by(func.count(BorrowSlip.id).desc()).limit(5).all()

    return render_template('staff/dashboard.html',
                           total_books=total_books,
                           pending_count=pending_count,
                           return_pending_count=return_pending_count,
                           borrowing_count=borrowing_count,
                           overdue_count=overdue_count,
                           requests=recent_requests,
                           return_requests=return_requests,
                           current_time=now,
                           low_stock_books=low_stock_books,
                           top_books=top_books,
                           now=datetime.now())


@main_bp.route('/request-borrow/<int:book_id>', methods=['POST'])
def request_borrow(book_id):
    return f"Yêu cầu mượn sách ID {book_id} đã được gửi (Tính năng đang phát triển)"

@main_bp.route("/search")
def search():
    search_query = request.args.get('q', '')
    category = request.args.get('category', '')
    language = request.args.get('language', '')
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
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

    full_name = f"{(current_user.last_name or '').strip()} {(current_user.first_name or '').strip()}".strip()
    user_display_name = full_name or current_user.username or current_user.email

    return render_template('user/history.html', history=history, user_display_name=user_display_name)


def _is_staff_or_admin():
    return current_user.is_authenticated and current_user.role in (RoleEnum.STAFF, RoleEnum.ADMIN)


@main_bp.route('/staff/request/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_borrow_request(request_id):
    if not _is_staff_or_admin():
        return abort(403)

    borrow_request = BorrowRequest.query.get_or_404(request_id)
    if borrow_request.status != RequestStatusEnum.Pending:
        flash('Yêu cầu này đã được xử lý trước đó.', 'warning')
        return redirect(url_for('main.staff_dashboard'))

    quantity = borrow_request.quantity or 1
    if borrow_request.book.available_quantity < quantity:
        flash('Không đủ số lượng sách để duyệt yêu cầu.', 'danger')
        return redirect(url_for('main.staff_dashboard'))

    borrow_request.status = RequestStatusEnum.Approved
    borrow_date = borrow_request.borrow_from_date or date.today()
    due_date = borrow_request.borrow_to_date or (borrow_date + timedelta(days=7))

    borrow_slip = BorrowSlip(
        user_id=borrow_request.user_id,
        book_id=borrow_request.book_id,
        borrow_request_id=borrow_request.id,
        borrow_date=borrow_date,
        due_date=due_date,
        quantity=quantity,
        status=BorrowStatusEnum.Borrowing
    )
    db.session.add(borrow_slip)
    borrow_request.book.available_quantity -= quantity
    db.session.commit()

    EmailService.send_approve_notification(
        borrow_request.user.first_name,
        borrow_request.user.email,
        borrow_request.book.title,
        due_date.strftime('%d/%m/%Y')
    )

    flash('Đã duyệt yêu cầu mượn và trừ tồn kho thành công.', 'success')
    return redirect(url_for('main.staff_dashboard'))


@main_bp.route('/staff/request/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_borrow_request(request_id):
    if not _is_staff_or_admin():
        return abort(403)

    borrow_request = BorrowRequest.query.get_or_404(request_id)
    if borrow_request.status != RequestStatusEnum.Pending:
        flash('Yêu cầu này đã được xử lý trước đó.', 'warning')
        return redirect(url_for('main.staff_dashboard'))

    borrow_request.status = RequestStatusEnum.Rejected
    db.session.commit()

    from app.services.email_service import EmailService
    EmailService.send_reject_notification(
        borrow_request.user.first_name,
        borrow_request.user.email,
        borrow_request.book.title,
        "Yêu cầu không phù hợp hoặc sách hiện không khả dụng."
    )

    flash('Đã từ chối yêu cầu mượn.', 'info')
    return redirect(url_for('main.staff_dashboard'))


@main_bp.route('/history/return/<int:request_id>', methods=['POST'])
@login_required
def return_book(request_id):
    borrow_request = BorrowRequest.query.filter_by(id=request_id, user_id=current_user.id).first_or_404()
    borrow_slip = borrow_request.borrow_slip

    if not borrow_slip or borrow_slip.status != BorrowStatusEnum.Borrowing:
        flash('Yêu cầu này chưa ở trạng thái đang mượn để trả sách.', 'warning')
        return redirect(url_for('main.borrow_history'))

    if borrow_slip.return_requested:
        flash('Yêu cầu trả sách của bạn đang chờ nhân viên duyệt.', 'info')
        return redirect(url_for('main.borrow_history'))

    borrow_slip.return_requested = True
    db.session.commit()

    flash('Đã gửi yêu cầu trả sách. Vui lòng chờ nhân viên duyệt.', 'success')
    return redirect(url_for('main.borrow_history'))


@main_bp.route('/staff/return/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_return_request(request_id):
    if not _is_staff_or_admin():
        return abort(403)

    borrow_request = BorrowRequest.query.get_or_404(request_id)
    borrow_slip = borrow_request.borrow_slip
    if not borrow_slip or borrow_slip.status != BorrowStatusEnum.Borrowing or not borrow_slip.return_requested:
        flash('Yêu cầu trả sách không hợp lệ hoặc đã được xử lý.', 'warning')
        return redirect(url_for('main.staff_dashboard'))

    borrow_slip.return_requested = False
    borrow_slip.status = BorrowStatusEnum.Returned
    borrow_slip.return_date = date.today()
    borrow_request.status = RequestStatusEnum.Completed
    borrow_request.book.available_quantity += (borrow_slip.quantity or 1)
    db.session.commit()

    flash('Đã duyệt trả sách thành công.', 'success')
    return redirect(request.referrer or url_for('main.staff_dashboard'))


@main_bp.route('/book/review/<int:book_id>', methods=['POST'])
@login_required
def add_review(book_id):
    from app.models import Review
    content = request.form.get('content')
    rating = request.form.get('rating', type=int)
    
    if not content or not rating:
        flash('Vui lòng nhập nội dung và chọn số sao.', 'warning')
        return redirect(url_for('main.book_detail', book_id=book_id))
    
    existing_review = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if existing_review:
        existing_review.content = content
        existing_review.rating = rating
        flash('Đánh giá của bạn đã được cập nhật.', 'success')
    else:
        new_review = Review(
            content=content,
            rating=rating,
            user_id=current_user.id,
            book_id=book_id
        )
        db.session.add(new_review)
        flash('Cảm ơn bạn đã đánh giá sách!', 'success')
        
    db.session.commit()
    return redirect(url_for('main.book_detail', book_id=book_id))

@main_bp.route('/reviews')
def all_reviews():
    from app.models import Review
    rev_id = request.args.get('id', type=int)
    is_ajax = request.args.get('ajax', type=int)
    
    all_revs = Review.query.order_by(Review.created_at.desc()).all()
    
    selected_rev = Review.query.get(rev_id) if rev_id else (all_revs[0] if all_revs else None)
    
    # Đánh dấu là đã đọc nếu người dùng xem
    if selected_rev and not selected_rev.is_read:
        selected_rev.is_read = True
        db.session.commit()
        
    if is_ajax:
        return render_template('user/partials/review_detail.html', selected_rev=selected_rev)
        
    return render_template('user/reviews.html', all_reviews=all_revs, selected_rev=selected_rev)

@main_bp.route('/reviews/mark-all-read')
def mark_all_reviews_read():
    from app.models import Review
    Review.query.filter_by(is_read=False).update({Review.is_read: True})
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('ajax'):
        return jsonify({'success': True})
    return redirect(request.referrer or url_for('main.all_reviews'))

@main_bp.route('/notifications/mark-all-read')
@login_required
def mark_all_notifications_read():
    from app.models import Notification
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('ajax'):
        return jsonify({'success': True})
    return redirect(request.referrer or url_for('user.notifications'))