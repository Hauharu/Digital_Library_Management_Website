import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
import requests
from flask import current_app, url_for
from app.models import Payment, PaymentMethodEnum, PaymentStatusEnum, Invoice, InvoiceStatusEnum, db

class PaymentService:
    @staticmethod
    def sync_invoice_amount(invoice):
        from app.models import IncidentReport, BorrowStatusEnum, db
        from datetime import date
        
        slip = invoice.borrow_slip
        if not slip:
            return

        today = date.today()
        overdue_fine = 0
        if slip.status.name != 'Returned' and today > slip.due_date:
            overdue_fine = (today - slip.due_date).days * 5000
        elif slip.status.name == 'Returned' and slip.return_date and slip.return_date > slip.due_date:
            overdue_fine = (slip.return_date - slip.due_date).days * 5000
            
        incident_fine = db.session.query(db.func.sum(IncidentReport.fine_amount)).filter_by(borrow_slip_id=slip.id).scalar() or 0
        
        invoice.amount = incident_fine + overdue_fine
        db.session.commit()

    @staticmethod
    def generate_vnpay_url(invoice_id, amount, ip_address):
        from app.services.vnpay_official import vnpay
        
        if ip_address == "::1" or ip_address == "127.0.0.1":
            ip_address = "127.0.0.1"
            
        vnp = vnpay()
        vnp.requestData['vnp_Version'] = '2.1.0'
        vnp.requestData['vnp_Command'] = 'pay'
        vnp.requestData['vnp_TmnCode'] = current_app.config.get("VNPAY_TMN_CODE", "").strip()
        vnp.requestData['vnp_Amount'] = int(amount * 100)
        vnp.requestData['vnp_CurrCode'] = 'VND'
        vnp.requestData['vnp_TxnRef'] = str(invoice_id)
        vnp.requestData['vnp_OrderInfo'] = f"Thanh toan hoa don {invoice_id}"
        vnp.requestData['vnp_OrderType'] = 'other'
        vnp.requestData['vnp_Locale'] = 'vn'
        vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
        vnp.requestData['vnp_IpAddr'] = ip_address
        vnp.requestData['vnp_ReturnUrl'] = current_app.config.get("VNPAY_RETURN_URL", "").strip()
        
        vnpay_payment_url = vnp.get_payment_url(
            current_app.config.get('VNPAY_PAYMENT_URL'), 
            current_app.config.get('VNPAY_HASH_SECRET', "").strip()
        )
        
        print(f"DEBUG VNPAY - OFFICIAL CLASS URL: {vnpay_payment_url}")
        return vnpay_payment_url

    @staticmethod
    def get_paypal_access_token():
        client_id = current_app.config["PAYPAL_CLIENT_ID"]
        client_secret = current_app.config["PAYPAL_CLIENT_SECRET"]
        url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        
        response = requests.post(
            url,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json", "Accept-Language": "en_US"}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        return None

    @staticmethod
    def create_paypal_payment(invoice_id, amount):
        access_token = PaymentService.get_paypal_access_token()
        if not access_token:
            return None

        amount_usd = round(amount / 25000, 2)
        if amount_usd < 0.01: amount_usd = 0.01

        url = "https://api-m.sandbox.paypal.com/v1/payments/payment"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payment_data = {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": str(amount_usd), "currency": "USD"},
                "description": f"Thanh toan hoa don {invoice_id}"
            }],
            "redirect_urls": {
                "return_url": url_for("user.paypal_return", _external=True),
                "cancel_url": url_for("user.paypal_cancel", _external=True)
            }
        }
        
        response = requests.post(url, json=payment_data, headers=headers)
        if response.status_code == 201:
            return response.json()
        return None

    @staticmethod
    def execute_paypal_payment(payment_id, payer_id):
        access_token = PaymentService.get_paypal_access_token()
        if not access_token:
            return False

        url = f"https://api-m.sandbox.paypal.com/v1/payments/payment/{payment_id}/execute"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.post(url, json={"payer_id": payer_id}, headers=headers)
        return response.status_code == 200

    @staticmethod
    def process_offline_payment(invoice_id):
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return False, "Không tìm thấy hóa đơn."
        
        invoice.status = InvoiceStatusEnum.Offline
        
        payment = Payment(
            amount_paid=invoice.amount,
            method=PaymentMethodEnum.Cash,
            status=PaymentStatusEnum.Completed,
            transaction_id=f"OFFLINE_{invoice_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            invoice_id=invoice_id,
            notes="Độc giả chọn thanh toán tại quầy."
        )
        db.session.add(payment)
        
        # Thông báo cho Staff
        from app.models import User, RoleEnum, Notification
        from app import socketio
        staff_users = User.query.filter(User.role.in_([RoleEnum.STAFF, RoleEnum.ADMIN])).all()
        user_name = f"{invoice.borrow_slip.user.last_name} {invoice.borrow_slip.user.first_name}"
        for staff in staff_users:
            notif = Notification(
                user_id=staff.id,
                title="Yêu cầu thanh toán Offline",
                content=f"Độc giả {user_name} chọn thanh toán tiền mặt cho hóa đơn #{invoice.id}",
                type="SYSTEM"
            )
            db.session.add(notif)
        db.session.commit()

        for staff in staff_users:
            unread_count = Notification.query.filter_by(user_id=staff.id, is_read=False).count()
            socketio.emit('update_notifications', {
                'unread_count': unread_count,
                'new_notification': {
                    'title': "Yêu cầu thanh toán Offline",
                    'content': f"Độc giả {user_name} chọn thanh toán tiền mặt cho hóa đơn #{invoice.id}",
                    'time': 'Vừa xong'
                }
            }, room=f"user_{staff.id}")

        return True, ""

    @staticmethod
    def validate_vnpay_return(data):
        from app.services.vnpay_official import vnpay
        vnp = vnpay()
        vnp.responseData = data.copy()
        hash_secret = current_app.config.get("VNPAY_HASH_SECRET", "").strip()
        return vnp.validate_response(hash_secret)

    @staticmethod
    def process_vnpay_result(data):
        if not PaymentService.validate_vnpay_return(data):
            return False, "Chữ ký không hợp lệ."

        vnp_ResponseCode = data.get("vnp_ResponseCode")
        txn_ref = data.get("vnp_TxnRef")
        try:
            invoice_id = int(txn_ref)
        except (ValueError, TypeError):
            return False, "Mã giao dịch không hợp lệ."
            
        amount = float(data.get("vnp_Amount")) / 100

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return False, "Không tìm thấy hóa đơn."

        if vnp_ResponseCode == "00":
            invoice.status = InvoiceStatusEnum.Paid
            payment = Payment(
                amount_paid=amount,
                method=PaymentMethodEnum.VNPay,
                status=PaymentStatusEnum.Completed,
                transaction_id=data.get("vnp_TransactionNo"),
                invoice_id=invoice_id,
                notes=f"Thanh toán qua VNPay thành công. Mã GD: {data.get('vnp_BankTranNo')}"
            )
            db.session.add(payment)
            
            # Thông báo cho Staff
            from app.models import User, RoleEnum, Notification
            from app import socketio
            staff_users = User.query.filter(User.role.in_([RoleEnum.STAFF, RoleEnum.ADMIN])).all()
            user_name = f"{invoice.borrow_slip.user.last_name} {invoice.borrow_slip.user.first_name}"
            for staff in staff_users:
                notif = Notification(
                    user_id=staff.id,
                    title="Thanh toán Online thành công",
                    content=f"Độc giả {user_name} đã thanh toán thành công hóa đơn #{invoice.id} qua VNPay",
                    type="SYSTEM"
                )
                db.session.add(notif)
            db.session.commit()

            for staff in staff_users:
                unread_count = Notification.query.filter_by(user_id=staff.id, is_read=False).count()
                socketio.emit('update_notifications', {
                    'unread_count': unread_count,
                    'new_notification': {
                        'title': "Hóa đơn đã thanh toán",
                        'content': f"Độc giả {user_name} đã thanh toán thành công hóa đơn #{invoice.id} qua VNPay",
                        'time': 'Vừa xong'
                    }
                }, room=f"user_{staff.id}")

            return True, ""
        else:
            return False, f"Thanh toán thất bại. Mã lỗi: {vnp_ResponseCode}"
