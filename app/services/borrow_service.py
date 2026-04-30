from datetime import date

from app import db
from app.models import BorrowRequest, BorrowSlip, BorrowStatusEnum, RequestStatusEnum


class BorrowService:
    @staticmethod
    def create_borrow_request(user, book, start_date, end_date, quantity):
        if quantity <= 0:
            return {'ok': False, 'message': 'Số lượng mượn phải lớn hơn 0.', 'category': 'danger'}

        if start_date < date.today():
            return {'ok': False, 'message': 'Ngày mượn không được nhỏ hơn ngày hiện tại.', 'category': 'danger'}

        if end_date <= start_date:
            return {'ok': False, 'message': 'Ngày trả phải lớn hơn ngày mượn.', 'category': 'danger'}

        available_quantity = book.available_quantity or 0
        if quantity > available_quantity:
            return {'ok': False, 'message': 'Số lượng mượn vượt quá số lượng còn trong kho.', 'category': 'danger'}

        active_slip = BorrowSlip.query.filter_by(
            user_id=user.id,
            book_id=book.id,
            status=BorrowStatusEnum.Borrowing
        ).first()
        if active_slip:
            return {'ok': False, 'message': 'Bạn đang mượn cuốn sách này.', 'category': 'warning'}

        active_request = BorrowRequest.query.filter_by(
            user_id=user.id,
            book_id=book.id
        ).filter(BorrowRequest.status.in_([RequestStatusEnum.Pending, RequestStatusEnum.Approved])).first()
        if active_request:
            return {'ok': False, 'message': 'Bạn đã có yêu cầu mượn đang chờ xử lý.', 'category': 'warning'}

        borrow_request = BorrowRequest(
            user_id=user.id,
            book_id=book.id,
            borrow_from_date=start_date,
            borrow_to_date=end_date,
            quantity=quantity,
            status=RequestStatusEnum.Pending
        )
        db.session.add(borrow_request)
        
        # Thông báo cho tất cả Staff/Admin
        from app.models import User, RoleEnum, Notification
        from app import socketio
        staff_users = User.query.filter(User.role.in_([RoleEnum.STAFF, RoleEnum.ADMIN])).all()
        for staff in staff_users:
            notif = Notification(
                user_id=staff.id,
                title="Yêu cầu mượn mới",
                content=f"Độc giả {user.last_name} {user.first_name} yêu cầu mượn '{book.title}'",
                type="SYSTEM"
            )
            db.session.add(notif)
        
        db.session.commit()

        # Thông báo cho chính người dùng
        notif_user = Notification(
            user_id=user.id,
            title="Yêu cầu mượn đã gửi",
            content=f"Yêu cầu mượn cuốn '{book.title}' của bạn đang chờ thủ thư duyệt.",
            type="SYSTEM"
        )
        db.session.add(notif_user)
        db.session.commit()

        # Emit socket cho chính người dùng
        unread_count_user = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        socketio.emit('update_notifications', {
            'unread_count': unread_count_user,
            'new_notification': {
                'title': "Yêu cầu mượn đã gửi",
                'time': 'Vừa xong',
                'id': notif_user.id
            }
        }, room=f"user_{user.id}")

        # Emit socket cho từng staff (nếu họ đang online)
        for staff in staff_users:
            unread_count = Notification.query.filter_by(user_id=staff.id, is_read=False).count()
            socketio.emit('update_notifications', {
                'unread_count': unread_count,
                'new_notification': {
                    'title': "Yêu cầu mượn mới",
                    'content': f"Độc giả {user.last_name} {user.first_name} yêu cầu mượn '{book.title}'",
                    'time': 'Vừa xong',
                    'id': None
                }
            }, room=f"user_{staff.id}")

        return {
            'ok': True,
            'message': (
                f'Đã tạo yêu cầu mượn "{book.title}" ({quantity} cuốn) '
                f'từ {start_date.strftime("%d/%m/%Y")} đến {end_date.strftime("%d/%m/%Y")}.'
            ),
            'category': 'success'
        }
