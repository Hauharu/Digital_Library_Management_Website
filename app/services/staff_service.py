from app import db, socketio
from app.models import BorrowSlip, Book, Invoice, InvoiceStatusEnum, BorrowRequest, \
    RequestStatusEnum, Notification, BorrowStatusEnum
from datetime import datetime
from app.services.email_service import EmailService


class StaffService:
    @staticmethod
    def get_active_orders(search_query=None, status_filter=None, date_filter=None):
        query = BorrowSlip.query.filter(BorrowSlip.status != BorrowStatusEnum.Returned)

        if search_query:
            clean_id = search_query.lower().replace('MS-', '').lstrip('0')
            from app.models import User  # Tránh circular import nếu cần
            query = query.join(User).join(Book).filter(
                db.or_(
                    User.last_name.ilike(f"%{search_query}%"),
                    Book.title.ilike(f"%{search_query}%"),
                    db.cast(BorrowSlip.id, db.String).contains(clean_id if clean_id else search_query)
                )
            )

        if status_filter:
            query = query.filter(BorrowSlip.status == status_filter)

        if date_filter:
            try:
                f_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(BorrowSlip.borrow_date == f_date)
            except:
                pass

        active_slips = query.order_by(BorrowSlip.due_date.asc()).all()
        today = datetime.now().date()

        for slip in active_slips:
            slip.is_late = slip.due_date < today
            slip.fine = (today - slip.due_date).days * 5000 if slip.is_late else 0
            # Lấy lịch sử 5 lần trả gần nhất của user này
            slip.user_history = BorrowSlip.query.filter_by(
                user_id=slip.user_id, status=BorrowStatusEnum.Returned
            ).order_by(BorrowSlip.return_date.desc()).limit(5).all()

        return active_slips

    @staticmethod
    def process_return(slip_id):
        slip = BorrowSlip.query.get_or_404(slip_id)
        book = Book.query.get(slip.book_id)
        now = datetime.now()
        fine_amount = 0

        if now.date() > slip.due_date:
            days_late = (now.date() - slip.due_date).days
            fine_amount = days_late * 5000
            new_invoice = Invoice(amount=fine_amount, issue_date=now, status=InvoiceStatusEnum.Paid,
                                  borrow_slip_id=slip.id)
            db.session.add(new_invoice)

        slip.status = BorrowStatusEnum.Returned
        slip.return_date = now.date()
        book.available_quantity += slip.quantity
        db.session.commit()

        # Gửi Email qua EmailService
        EmailService.send_return_confirmation(slip.user.first_name, slip.user.email, book.title, fine_amount)
        return book.title

    @staticmethod
    def process_approve(request_id):
        borrow_req = BorrowRequest.query.get_or_404(request_id)
        book = Book.query.get(borrow_req.book_id)

        if book.available_quantity < borrow_req.quantity:
            return False, f"Sách '{book.title}' không đủ số lượng!"

        new_slip = BorrowSlip(
            borrow_date=datetime.now().date(),
            due_date=borrow_req.borrow_to_date,
            quantity=borrow_req.quantity,
            status=BorrowStatusEnum.Borrowing,
            user_id=borrow_req.user_id,
            book_id=borrow_req.book_id,
            borrow_request_id=borrow_req.id
        )

        borrow_req.status = RequestStatusEnum.Completed
        book.available_quantity -= borrow_req.quantity

        notif = Notification(
            user_id=borrow_req.user_id,
            title="Yêu cầu mượn sách đã được duyệt",
            content=f"Cuốn '{book.title}' đã sẵn sàng để bạn đến lấy.",
            type="SYSTEM"
        )

        db.session.add(new_slip)
        db.session.add(notif)
        db.session.commit()

        # SocketIO thông báo realtime
        unread_count = Notification.query.filter_by(user_id=borrow_req.user_id, is_read=False).count()
        socketio.emit('update_notifications', {
            'unread_count': unread_count,
            'new_notification': {'title': notif.title, 'time': 'Vừa xong', 'id': notif.id}
        }, room=f"user_{borrow_req.user_id}")

        # Email thông báo
        EmailService.send_approve_notification(borrow_req.reader.first_name, borrow_req.reader.email, book.title,
                                               new_slip.due_date)

        return True, borrow_req.reader.first_name

    @staticmethod
    def process_reject(request_id, reason):
        req = BorrowRequest.query.get_or_404(request_id)
        req.status = RequestStatusEnum.Rejected
        req.reject_reason = reason

        notif = Notification(
            user_id=req.user_id,
            title="Yêu cầu mượn sách bị từ chối",
            content=f"Lý do: {reason}",
            type="SYSTEM"
        )
        db.session.add(notif)
        db.session.commit()

        # SocketIO
        unread_count = Notification.query.filter_by(user_id=req.user_id, is_read=False).count()
        socketio.emit('update_notifications', {
            'unread_count': unread_count,
            'new_notification': {'title': notif.title, 'time': 'Vừa xong'}
        }, room=f"user_{req.user_id}")

        # Email
        EmailService.send_reject_notification(req.reader.first_name, req.reader.email, req.book.title, reason)
        return True

    @staticmethod
    def notify_overdue_slips():
        from app.models import BorrowSlip, BorrowStatusEnum
        today = datetime.now().date()
        # Tìm tất cả phiếu đang mượn và đã quá hạn
        overdue_slips = BorrowSlip.query.filter(
            BorrowSlip.status == BorrowStatusEnum.Borrowing,
            BorrowSlip.due_date < today
        ).all()

        count = 0
        for slip in overdue_slips:
            days_late = (today - slip.due_date).days
            fine = days_late * 5000
            EmailService.send_overdue_warning(
                slip.user.first_name,
                slip.user.email,
                slip.book.title,
                slip.due_date,
                fine
            )
            count += 1
        return count