from flask import Blueprint, render_template
from app.models import Book

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_books = Book.query.limit(8).all()
    return render_template('index.html', featured_books=featured_books)

@main_bp.route('/book-detail/<int:book_id>')
def book_detail(book_id):
    # Lấy thông tin sách từ DB theo ID
    book = Book.query.get_or_404(book_id)
    
    # Đảm bảo có các thuộc tính cho template (vì model dùng available_quantity và id)
    if not hasattr(book, 'quantity'):
        setattr(book, 'quantity', book.available_quantity)
    if not hasattr(book, 'book_id'):
        setattr(book, 'book_id', book.id)
            
    # Lấy sách liên quan (cùng danh mục, tối đa 6 cuốn, loại trừ sách hiện tại)
    related_books = Book.query.filter(Book.category_id == book.category_id, Book.id != book.id).limit(6).all()
    
    # Tính toán trạng thái của người dùng đối với cuốn sách này
    from flask_login import current_user
    from app.models import BorrowRequest, BorrowSlip, RequestStatusEnum, BorrowStatusEnum
    
    user_state = {
        'is_borrowing': False,
        'request_status': None
    }
    
    if current_user.is_authenticated:
        # Kiểm tra xem có đang mượn không
        active_slip = BorrowSlip.query.filter_by(user_id=current_user.id, book_id=book.id, status=BorrowStatusEnum.Borrowing).first()
        if active_slip:
            user_state['is_borrowing'] = True
        else:
            # Kiểm tra yêu cầu chờ duyệt hoặc đã duyệt
            active_request = BorrowRequest.query.filter_by(user_id=current_user.id, book_id=book.id).filter(
                BorrowRequest.status.in_([RequestStatusEnum.Pending, RequestStatusEnum.Approved])
            ).first()
            if active_request:
                user_state['request_status'] = 'pending' if active_request.status == RequestStatusEnum.Pending else 'approved'
            
    return render_template('book/book_detail.html', book=book, related_books=related_books, user_state=user_state)

@main_bp.route('/request-borrow/<int:book_id>', methods=['POST'])
def request_borrow(book_id):
    # Placeholder for borrowing logic
    return f"Yêu cầu mượn sách ID {book_id} đã được gửi (Tính năng đang phát triển)"
