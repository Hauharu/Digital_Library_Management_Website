from flask_mail import Message
from threading import Thread
from flask import current_app, render_template
from app import mail

class EmailService:
    @staticmethod
    def send_async_email(app, msg):
        with app.app_context():
            mail.send(msg)

    @staticmethod
    def send_mail(subject, recipient, html_body):
        app = current_app._get_current_object()
        msg = Message(subject, recipients=[recipient])
        msg.html = html_body
        Thread(target=EmailService.send_async_email, args=(app, msg)).start()

    @classmethod
    def send_approve_notification(cls, reader_name, reader_email, book_title, due_date):
        subject = f"[OU BOOK] Yêu cầu mượn sách '{book_title}' đã được duyệt"
        html_content = f"""
            <div style="font-family: sans-serif; line-height: 1.6;">
                <h2 style="color: #2c3e50;">Chào {reader_name}!</h2>
                <p>Yêu cầu mượn sách của bạn đã được phê duyệt.</p>
                <p><b>Sách:</b> {book_title}<br>
                <b>Hạn trả dự kiến:</b> {due_date}</p>
                <p>Vui lòng đến quầy thư viện để nhận sách.</p>
                <hr><small>Email tự động từ hệ thống OU BOOK</small>
            </div>
        """
        cls.send_mail(subject, reader_email, html_content)

    @classmethod
    def send_reject_notification(cls, reader_name, reader_email, book_title, reason):
        subject = f"[OU BOOK] Thông báo từ chối yêu cầu mượn sách"
        html_content = f"""
            <div style="font-family: sans-serif; line-height: 1.6;">
                <h2 style="color: #e74c3c;">Chào {reader_name}</h2>
                <p>Yêu cầu mượn cuốn <b>{book_title}</b> đã bị từ chối.</p>
                <p><b>Lý do:</b> {reason}</p>
                <p>Vui lòng liên hệ thủ thư nếu cần hỗ trợ thêm.</p>
            </div>
        """
        cls.send_mail(subject, reader_email, html_content)

    @classmethod
    def send_return_confirmation(cls, reader_name, reader_email, book_title, fine_amount=0):
        subject = f"[OU BOOK] Xác nhận trả sách thành công"
        fine_html = f"<p style='color:red;'>Phí phạt chậm trả: {fine_amount:,.0f} VNĐ</p>" if fine_amount > 0 else ""
        html_content = f"""
            <div style="font-family: sans-serif; line-height: 1.6;">
                <h2>Xác nhận trả sách</h2>
                <p>Chào {reader_name}, thư viện đã nhận lại cuốn: <b>{book_title}</b>.</p>
                {fine_html}
                <p>Cảm ơn bạn đã đọc sách tại OU BOOK!</p>
            </div>
        """
        cls.send_mail(subject, reader_email, html_content)


    @classmethod
    def send_overdue_warning(cls, reader_name, reader_email, book_title, due_date, fine_amount):
        subject = f"[OU BOOK] CẢNH BÁO: Sách mượn đã quá hạn trả!"
        html_content = f"""
            <div style="font-family: sans-serif; line-height: 1.6; color: #721c24;">
                <h2 style="color: #dc3545;">Thông báo quá hạn mượn sách</h2>
                <p>Chào {reader_name},</p>
                <p>Hệ thống ghi nhận cuốn sách <b>{book_title}</b> của bạn đã quá hạn từ ngày <b>{due_date}</b>.</p>
                <p>Tiền phạt tính đến hiện tại: <b>{fine_amount:,.0f} VNĐ</b>.</p>
                <p>Vui lòng mang sách trả lại thư viện sớm nhất để tránh phát sinh thêm phí phạt.</p>
                <hr><small>Đây là thông báo tự động từ OU BOOK</small>
            </div>
        """
        cls.send_mail(subject, reader_email, html_content)


    @classmethod
    def send_general_notification(cls, reader_name, reader_email, title, content):
        subject = f"[OU BOOK] {title}"
        html_content = f"""
            <div style="font-family: sans-serif; line-height: 1.6;">
                <h2 style="color: #3498db;">{title}</h2>
                <p>Chào {reader_name},</p>
                <p>{content}</p>
                <hr>
                <small>Hệ thống thư viện số OU BOOK</small>
            </div>
        """
        cls.send_mail(subject, reader_email, html_content)