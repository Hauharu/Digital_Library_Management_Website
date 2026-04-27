from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import BorrowRequest, RequestStatusEnum
from app.services.staff_service import StaffService
from flask_login import login_required

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