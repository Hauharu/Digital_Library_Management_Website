from flask import Blueprint, render_template,abort
from app.models import RoleEnum, User, Book, BorrowRequest
from flask_login import login_required, current_user
from app.decorators import role_required
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured_books = Book.query.limit(8).all()
    return render_template('index.html', featured_books=featured_books)

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


@main_bp.route('/staff')
@login_required
@role_required(RoleEnum.STAFF)
def staff_dashboard():
    pending_list = BorrowRequest.query.filter_by(status='pending').all()
    return render_template('staff/dashboard.html', requests=pending_list)