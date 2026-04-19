from flask import Blueprint, request, jsonify, render_template
from app.services.auth_service import register_user


auth_bp = Blueprint('auth', __name__,url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')

    data = request.form

    result = register_user(data)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 201

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    # For now, just a placeholder for POST login
    return jsonify({"message": "Login not implemented yet"}), 501
