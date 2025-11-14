from flask import Blueprint, request, jsonify
from app.auth.services import create_user_service, verify_user_service
from flask_login import login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register_api', methods=['POST'])
def register_api():
    data = request.get_json()
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({"msg": "Faltan datos requeridos (username, email, password)."}), 400

    return create_user_service(
        data['username'],
        data['email'],
        data['password']
    )

@auth_bp.route('/login_api', methods=['POST'])
def login_api():
    data = request.get_json()
    if not data or not all(k in data for k in ('username_or_email', 'password')):
        return jsonify({"msg": "Faltan datos requeridos (username_or_email, password)."}), 400

    return verify_user_service(
        data['username_or_email'],
        data['password']
    )

@auth_bp.route('/test_auth', methods=['GET'])
@login_required
def test_auth():
    return jsonify({
        "msg": "Autenticación exitosa",
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.name
    }), 200
