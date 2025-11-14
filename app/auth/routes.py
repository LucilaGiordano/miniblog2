from flask import Blueprint, request, jsonify
from .services import create_user_service, verify_user_service
from flask_login import login_required, current_user

# Definición del Blueprint de Autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register_api', methods=['POST'])
def register_api():
    """Ruta API para registrar un nuevo usuario y obtener un token JWT."""
    data = request.get_json()
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({"msg": "Faltan datos requeridos (username, email, password)."}), 400

    username = data['username']
    email = data['email']
    password = data['password']

    return create_user_service(username, email, password)

@auth_bp.route('/login_api', methods=['POST'])
def login_api():
    """Ruta API para iniciar sesión y obtener un token JWT."""
    data = request.get_json()
    if not data or not all(k in data for k in ('username_or_email', 'password')):
        return jsonify({"msg": "Faltan datos requeridos (username_or_email, password)."}), 400

    username_or_email = data['username_or_email']
    password = data['password']

    return verify_user_service(username_or_email, password)

@auth_bp.route('/test_auth', methods=['GET'])
@login_required # Esto requiere que el usuario esté autenticado
def test_auth():
    """Ruta de prueba que solo funciona si el usuario ha iniciado sesión."""
    return jsonify({
        "msg": "Autenticación exitosa",
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.name
    }), 200