from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from app.services.auth_service import register_user
from app.models import RoleEnum, User, db
from flask_login import logout_user, login_required, current_user, login_user
from app import bcrypt, oauth
import secrets

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')

    data = request.form

    result = register_user(data)

    if "error" in result:
        return render_template('auth/register.html', error=result['error'])

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

    login_user(user)
    return redirect(url_for('main.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))