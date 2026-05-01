from app import db, socketio
from app.models import BorrowSlip, Book, Invoice, InvoiceStatusEnum, BorrowRequest, \
    RequestStatusEnum, Notification, BorrowStatusEnum,IncidentReport,IncidentTypeEnum, Category
from datetime import datetime
from app.services.email_service import EmailService
from datetime import datetime, timedelta
import cloudinary
import cloudinary.uploader

class StaffService:
    @staticmethod
    def get_active_orders(search_query=None, status_filter=None, date_filter=None):
        query = BorrowSlip.query.filter(BorrowSlip.status != BorrowStatusEnum.Returned)

        if search_query:
            clean_id = search_query.lower().replace('MS-', '').lstrip('0')
            from app.models import User
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
            overdue_fine = (today - slip.due_date).days * 5000 if slip.is_late else 0

            unpaid_invoices = [inv for inv in slip.invoices if inv.status.name in ['Pending', 'Offline', 'Overdue']]
            
            if unpaid_invoices:
                from app.services.payment_service import PaymentService
                for inv in unpaid_invoices:
                    PaymentService.sync_invoice_amount(inv)
                slip.fine = sum(inv.amount for inv in unpaid_invoices)
            else:
                slip.fine = overdue_fine

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
            
            # Kiểm tra xem đã có hóa đơn (ví dụ do báo sự cố trước đó) chưa
            existing_invoice = Invoice.query.filter_by(borrow_slip_id=slip.id).first()
            if existing_invoice:
                existing_invoice.amount += fine_amount
                existing_invoice.updated_at = now
            else:
                new_invoice = Invoice(amount=fine_amount, issue_date=now, status=InvoiceStatusEnum.Pending,
                                      borrow_slip_id=slip.id)
                db.session.add(new_invoice)

        slip.status = BorrowStatusEnum.Returned
        slip.return_date = now.date()
        
        # Cập nhật trạng thái yêu cầu mượn nếu có
        if slip.borrow_request:
            slip.borrow_request.status = RequestStatusEnum.Completed
        
        # Kiểm tra an toàn: Không để số lượng hiện có vượt quá tổng số lượng trong kho
        new_available = book.available_quantity + slip.quantity
        if new_available > book.total_quantity:
            book.available_quantity = book.total_quantity
        else:
            book.available_quantity = new_available
            
        db.session.commit()
        
        if fine_amount > 0:
            # Lấy tổng tiền phạt cuối cùng (bao gồm cả các khoản phạt hư hỏng nếu đã báo trước đó)
            final_invoice = Invoice.query.filter_by(borrow_slip_id=slip.id).first()
            total_fine = final_invoice.amount if final_invoice else fine_amount

            notif = Notification(
                user_id=slip.user_id,
                title="Thông báo phí phạt trả muộn",
                content=f"Bạn bị phạt {fine_amount:,.0f} VNĐ do trả sách '{book.title}' muộn {days_late} ngày.<br/>Tổng tiền phạt cần thanh toán là {total_fine:,.0f} VNĐ.",
                type="FINE"
            )
            db.session.add(notif)
            db.session.commit()
            
            unread_count = Notification.query.filter_by(user_id=slip.user_id, is_read=False).count()
            socketio.emit('update_notifications', {
                'unread_count': unread_count,
                'new_notification': {
                    'title': notif.title,
                    'content': notif.content,
                    'time': 'Vừa xong',
                    'id': notif.id
                }
            }, room=f"user_{slip.user_id}")

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
            'new_notification': {
                'title': notif.title, 
                'content': notif.content,
                'time': 'Vừa xong', 
                'id': notif.id
            }
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
            'new_notification': {
                'title': notif.title,
                'content': notif.content,
                'time': 'Vừa xong'
            }
        }, room=f"user_{req.user_id}")

        # Email
        EmailService.send_reject_notification(req.reader.first_name, req.reader.email, req.book.title, reason)
        return True

    @staticmethod
    def notify_overdue_slips():
        from app.models import BorrowSlip, BorrowStatusEnum
        today = datetime.now().date()
        # Tìm tất cả phiếu chưa trả và đã quá hạn (bao gồm cả trạng thái Đang mượn, Quá hạn, Hư hỏng)
        overdue_slips = BorrowSlip.query.filter(
            BorrowSlip.status.in_([BorrowStatusEnum.Borrowing, BorrowStatusEnum.Overdue, BorrowStatusEnum.Damaged]),
            BorrowSlip.due_date < today
        ).all()

        count = 0
        
        for slip in overdue_slips:
            days_late = (today - slip.due_date).days
            overdue_fine = days_late * 5000
            
            # Lấy tổng tiền thực tế từ hóa đơn để thông báo cho khớp 
            from app.models import Invoice
            invoice = Invoice.query.filter_by(borrow_slip_id=slip.id).first()
            display_fine = invoice.amount if invoice else overdue_fine
            
            
            EmailService.send_overdue_warning(
                slip.user.first_name,
                slip.user.email,
                slip.book.title,
                slip.due_date,
                display_fine
            )
            notif = Notification(
                user_id=slip.user_id,
                title="Cảnh báo sách quá hạn",
                content=f"Sách '{slip.book.title}' của bạn đã quá hạn.<br/>Tổng phí phạt hiện tại là {display_fine:,.0f} VNĐ.",
                type="WARNING"
            )
            db.session.add(notif)
            count += 1

            # Gửi thông báo Real-time
            from app import socketio
            unread_count = Notification.query.filter_by(user_id=slip.user_id, is_read=False).count()
            socketio.emit('update_notifications', {
                'unread_count': unread_count,
                'new_notification': {
                    'title': "Cảnh báo sách quá hạn",
                    'content': f"Sách '{slip.book.title}' của bạn đã quá hạn.<br/>Tổng phí phạt hiện tại là {display_fine:,.0f} VNĐ.",
                    'time': 'Vừa xong'
                }
            }, room=f"user_{slip.user_id}")

        db.session.commit()
        return count

    @staticmethod
    def report_incident(slip_id, damage_ratio, description, fine_amount):

        slip = BorrowSlip.query.get_or_404(slip_id)
        amount = float(fine_amount)

        try:
            ratio_val = float(damage_ratio)
        except (ValueError, TypeError):

            ratio_val = 0.5

        if ratio_val >= 1.0:
            inc_type = IncidentTypeEnum.LOST
            slip.status = BorrowStatusEnum.Lost
        else:
            inc_type = IncidentTypeEnum.DAMAGED
            slip.status = BorrowStatusEnum.Damaged

        # Xóa các IncidentReport cũ của phiếu này (nếu có) để tránh cộng dồn sai
        from app.models import IncidentReport
        IncidentReport.query.filter_by(borrow_slip_id=slip.id).delete()

        report = IncidentReport(
            borrow_slip_id=slip.id,
            type=inc_type,
            description=description,
            fine_amount=amount
        )
        db.session.add(report)

        # Tính toán lại tổng tiền phạt: Tiền quá hạn + Tiền sự cố mới
        today = datetime.now().date()
        overdue_fine = 0
        if slip.due_date < today:
            overdue_fine = (today - slip.due_date).days * 5000
        
        total_new_amount = overdue_fine + amount

        existing_invoice = Invoice.query.filter_by(borrow_slip_id=slip.id).first()
        if existing_invoice:
            existing_invoice.amount = total_new_amount
            existing_invoice.updated_at = datetime.now()
        else:
            new_invoice = Invoice(
                amount=total_new_amount,
                issue_date=datetime.now(),
                due_date=(today + timedelta(days=7)),
                status=InvoiceStatusEnum.Pending,
                borrow_slip_id=slip.id
            )
            db.session.add(new_invoice)

        db.session.commit()

        # Lấy tổng tiền phạt sau khi đã cập nhật
        total_fine = total_new_amount

        # Tạo thông báo hệ thống
        notif = Notification(
            user_id=slip.user_id,
            title=f"Phạt vi phạm: {inc_type.value}",
            content=f"Phạt {amount:,.0f} VNĐ cho sách '{slip.book.title}'. Lý do: {description}.<br/>Tổng tiền phạt hiện tại là {total_fine:,.0f} VNĐ.",
            type="FINE"
        )
        db.session.add(notif)
        db.session.commit()

        # SocketIO
        unread_count = Notification.query.filter_by(user_id=slip.user_id, is_read=False).count()
        socketio.emit('update_notifications', {
            'unread_count': unread_count,
            'new_notification': {
                'title': notif.title,
                'content': notif.content,
                'time': 'Vừa xong',
                'id': notif.id
            }
        }, room=f"user_{slip.user_id}")

        EmailService.send_general_notification(
            slip.user.first_name,
            slip.user.email,
            f"Thông báo xử lý sự cố sách: {slip.book.title}",
            f"Chúng tôi ghi nhận cuốn sách bạn mượn gặp sự cố: {inc_type.value}. "
            f"Số tiền phạt là: {amount:,.0f} VNĐ. Vui lòng thanh toán hóa đơn."
        )
        return True

    @staticmethod
    def create_book(data, image_file):
        try:
            image_url = None

            if image_file and image_file.filename != '':
                # Gọi hàm uploader của Cloudinary
                upload_result = cloudinary.uploader.upload(
                    image_file,
                    folder="library/books"  # Lưu vào thư mục này trên Cloudinary cho gọn
                )
                image_url = upload_result.get('secure_url')

            # Tạo đối tượng Book mới
            new_book = Book(
                title=data.get('title'),
                author=data.get('author'),
                category_id=data.get('category_id'),
                isbn=data.get('isbn'),
                price=data.get('price'),
                total_quantity=data.get('total_quantity'),
                available_quantity=data.get('total_quantity'),
                description=data.get('description'),
                image=image_url
            )

            db.session.add(new_book)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Lỗi khi thêm sách: {str(e)}")
            db.session.rollback()
            return False


    @staticmethod
    def update_book(book_id, data, image_file):
        book = Book.query.get(book_id)
        if not book: return False

        book.title = data.get('title')
        book.price = float(data.get('price'))

        # Logic: Nếu tăng tổng số lượng, số lượng sẵn có cũng tăng theo
        diff = int(data.get('total_quantity')) - book.total_quantity
        book.total_quantity = int(data.get('total_quantity'))
        book.available_quantity += diff

        if image_file:
            upload_result = cloudinary.uploader.upload(image_file)
            book.image = upload_result.get('url')

        db.session.commit()
        return True

    @staticmethod
    def get_all_books():
        return Book.query.options(
            db.selectinload(Book.category)
        ).order_by(Book.id.desc()).all()

    @staticmethod
    def get_all_categories():
        return Category.query.all()

    @staticmethod
    def get_book_by_id(book_id):
        return Book.query.get_or_404(book_id)

    @staticmethod
    def get_filtered_books(page=1, per_page=10, search_query='', category_id=None):
        query = Book.query

        if search_query:
            query = query.filter(
                db.or_(
                    Book.title.icontains(search_query),
                    Book.author.icontains(search_query),
                    Book.isbn.contains(search_query)
                )
            )

        if category_id and category_id != 'all':
            query = query.filter(Book.category_id == category_id)

        return query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page)

    @staticmethod
    def delete_book(book_id):
        book = Book.query.get(book_id)
        if not book:
            return False

        borrowing_count = any(slip.status.name == 'Borrowed' for slip in book.borrow_slips)
        if borrowing_count:
            return "cannot_delete_borrowed"

        try:
            db.session.delete(book)
            db.session.commit()
            return True
        except Exception:
            return False