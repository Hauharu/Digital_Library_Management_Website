from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import BorrowSlip, Book, User, BorrowStatusEnum, Invoice, InvoiceStatusEnum, BorrowRequest, \
    RequestStatusEnum
from datetime import datetime

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


@staff_bp.app_context_processor
def inject_pending_count():
    count = BorrowRequest.query.filter_by(status=RequestStatusEnum.Pending).count()
    return dict(pending_count=count)


@staff_bp.route('/orders')
def manage_orders():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    from_date = request.args.get('from_date', '')

    query = BorrowSlip.query.filter(BorrowSlip.status != BorrowStatusEnum.Returned)

    if search:
        clean_id = search.lower().replace('MS-', '').lstrip('0')
        query = query.join(User).join(Book).filter(
            db.or_(
                User.last_name.ilike(f"%{search}%"),
                Book.title.ilike(f"%{search}%"),
                db.cast(BorrowSlip.id, db.String).contains(clean_id if clean_id else search)
            )
        )

    if status:
        query = query.filter(BorrowSlip.status == status)

    if from_date:
        try:
            f_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(BorrowSlip.borrow_date == f_date)
        except:
            pass

    active_slips = query.order_by(BorrowSlip.due_date.asc()).all()
    today = datetime.now().date()

    for slip in active_slips:
        slip.is_late = slip.due_date < today
        slip.fine = (today - slip.due_date).days * 5000 if slip.is_late else 0

        slip.user_history = BorrowSlip.query.filter_by(
            user_id=slip.user_id,
            status=BorrowStatusEnum.Returned
        ).order_by(BorrowSlip.return_date.desc()).limit(5).all()

    return render_template('staff/staff_orders.html', active_slips=active_slips)


@staff_bp.route('/confirm-return/<int:slip_id>', methods=['POST'])
def confirm_return(slip_id):
    slip = BorrowSlip.query.get_or_404(slip_id)
    book = Book.query.get(slip.book_id)
    now = datetime.now()

    if now.date() > slip.due_date:
        days_late = (now.date() - slip.due_date).days
        fine_amount = days_late * 5000
        new_invoice = Invoice(amount=fine_amount, issue_date=now, status=InvoiceStatusEnum.Paid, borrow_slip_id=slip.id)
        db.session.add(new_invoice)

    slip.status = BorrowStatusEnum.Returned
    slip.return_date = now.date()
    book.available_quantity += slip.quantity

    db.session.commit()
    flash(f"Đã nhận trả sách: {book.title}", "success")
    return redirect(url_for('staff.manage_orders'))