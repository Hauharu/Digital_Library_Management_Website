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