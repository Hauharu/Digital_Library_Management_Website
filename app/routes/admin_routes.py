from sqlalchemy import func
from datetime import datetime
from app import db
from app.models import User, Book, Category, BorrowSlip, BorrowRequest, Invoice, RoleEnum, RequestStatusEnum, BorrowStatusEnum
from flask import Blueprint, render_template, request, abort
from app.decorators import role_required

admin_bp = Blueprint('admin', __name__,url_prefix='/admin')

@admin_bp.route('/dashboard')
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