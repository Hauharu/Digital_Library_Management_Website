from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.services.auth_service import register_user, login_user_logic


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
    return redirect(url_for('auth.login')) # Đăng ký xong thì qua trang login

    
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    data = request.form
    result = login_user_logic(data)

    if "error" in result:

        return render_template('auth/login.html', error=result['error'])


    flash(result['message'], 'success')
    return redirect(url_for('main.index')) 



@auth_bp.route('/logout')
def logout():
    result = logout_user()
    return jsonify(result), 200
