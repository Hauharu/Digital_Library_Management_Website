from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from app.services.auth_service import register_user
from app.models import RoleEnum, User, db
from flask_login import logout_user, login_required, current_user, login_user
from app import bcrypt, oauth
import secrets
from app.services.email_service import EmailService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')

    data = request.form

    result = register_user(data)

    if "error" in result:
        return render_template('auth/register.html', error=result['error'])

    user = User.query.filter_by(email=data.get('email')).first()
    if user:
        EmailService.send_general_notification(
            user.first_name,
            user.email,
            "Chào mừng bạn đến với OUBOOK",
            "Tài khoản của bạn đã được khởi tạo thành công. Hãy khám phá kho sách khổng lồ của chúng tôi ngay hôm nay!"
        )

    flash(result['message'], 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')

    email = request.form.get('email')
    password = request.form.get('password')


    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user)

        # Tạo thông báo đăng nhập mới
        from app.models import Notification
        from datetime import datetime
        new_notif = Notification(
            user_id=user.id,
            title="Một lượt đăng nhập mới vào tài khoản OUBOOK của bạn",
            content=f"""
                <p>Xin chào <strong>{user.last_name} {user.first_name}</strong>,</p>
                <p>Tài khoản OUBOOK của bạn đã được đăng nhập trên hệ thống với thông tin cụ thể như sau:</p>
                <ul>
                    <li><strong>Tài khoản:</strong> {user.email}</li>
                    <li><strong>Thời gian:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</li>
                    <li><strong>Thiết bị:</strong> {request.user_agent.string}</li>
                    <li><strong>IP:</strong> {request.remote_addr}</li>
                </ul>
                <p>Nếu đây là bạn, bạn không cần phải làm gì cả.</p>
                <p>Nếu bạn không làm điều này, vui lòng <a href='/auth/forgot-password'>thay đổi mật khẩu của bạn</a>.</p>
            """,
            type="security",
            sent_date=datetime.now()
        )
        db.session.add(new_notif)
        db.session.commit()

        EmailService.send_general_notification(
            user.first_name,
            user.email,
            "Cảnh báo đăng nhập mới",
            f"Tài khoản của bạn vừa được đăng nhập từ thiết bị: {request.user_agent.platform}. Nếu không phải bạn, hãy đổi mật khẩu ngay."
        )

        role = user.role.name

        if role == 'ADMIN':
            return redirect(url_for('admin.admin_dashboard'))
        elif role == 'STAFF':
            return redirect(url_for('main.staff_dashboard'))
        else:
            return redirect(url_for('main.index'))

    flash("Sai email hoặc mật khẩu", "danger")
    return redirect(url_for('auth.login'))


@auth_bp.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    resp = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
    user_info = resp.json()
    
    if not user_info:
        return redirect(url_for('auth.login'))

    email = user_info['email']
    user = User.query.filter_by(email=email).first()

    if not user:
        # Tạo người dùng mới nếu chưa tồn tại
        full_name = user_info.get('name', 'Google User')
        name_parts = full_name.split()
        first_name = name_parts[-1] if name_parts else 'User'
        last_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else 'Google'
        
        user = User(
            email=email,
            username=email,
            first_name=first_name,
            last_name=last_name,
            password=bcrypt.generate_password_hash(secrets.token_urlsafe(16)).decode('utf-8'),
            role=RoleEnum.READER,
            avatar=user_info.get('picture', "https://res.cloudinary.com/dwwfgtxv4/image/upload/v1776585521/AnhDaiDien_nvnfre.png")
        )
        db.session.add(user)
        db.session.commit()

        # Gửi thêm Email cảnh báo bảo mật
        EmailService.send_general_notification(
            user.first_name,
            user.email,
            "Cảnh báo đăng nhập mới",
            f"Tài khoản của bạn vừa được đăng nhập từ thiết bị: {request.user_agent.platform}. Nếu không phải bạn, hãy đổi mật khẩu ngay."
        )

    login_user(user)

    # Tạo thông báo đăng nhập mới (Google OAuth)
    from app.models import Notification
    from datetime import datetime
    new_notif = Notification(
        user_id=user.id,
        title="Đăng nhập mới vào tài khoản OUBOOK bằng Google",
        content=f"""
            <p>Xin chào <strong>{user.last_name} {user.first_name}</strong>,</p>
            <p>Bạn vừa đăng nhập thành công vào OUBOOK bằng tài khoản Google.</p>
            <ul>
                <li><strong>Email Google:</strong> {user.email}</li>
                <li><strong>Thời gian:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</li>
                <li><strong>Thiết bị:</strong> {request.user_agent.string}</li>
            </ul>
            <p>Nếu là bạn, hãy tiếp tục hành trình đọc sách của mình!</p>
        """,
        type="security",
        sent_date=datetime.now()
    )
    db.session.add(new_notif)
    db.session.commit()

    return redirect(url_for('main.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')

    email = request.form.get('email')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        flash("Mật khẩu xác nhận không khớp", "danger")
        return render_template('auth/forgot_password.html')

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Email không tồn tại trong hệ thống", "danger")
        return render_template('auth/forgot_password.html')

    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()

    EmailService.send_general_notification(
        user.first_name,
        user.email,
        "Mật khẩu của bạn đã được thay đổi",
        "Chúng tôi thông báo rằng mật khẩu tài khoản OUBOOK của bạn vừa được cập nhật thành công. Nếu bạn không thực hiện thay đổi này, hãy liên hệ hỗ trợ ngay lập tức."
    )

    flash("Đặt lại mật khẩu thành công! Vui lòng đăng nhập lại.", "success")
    return redirect(url_for('auth.login'))