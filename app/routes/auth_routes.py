from flask import Blueprint, request, jsonify, render_template
from app.services.auth_service import register_user
from app.models import RoleEnum, User
from flask_login import logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__,url_prefix='/auth')


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

from flask_login import login_user
from app.models import User
from app import bcrypt
from flask import request, render_template, redirect, url_for, flash

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


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))