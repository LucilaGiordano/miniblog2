import jwt
import datetime
from app import db
from .models import User, Role
from flask import current_app, jsonify

# Función para encontrar o crear roles
def get_or_create_role(role_name):
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.commit()
    return role

# Servicio para crear un nuevo usuario
def create_user_service(username, email, password):
    # 1. Verificar si el usuario ya existe
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"msg": "El nombre de usuario ya está en uso."}), 400
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"msg": "El correo electrónico ya está registrado."}), 400

    # 2. Asignar el rol por defecto (READER, ID=1)
    reader_role = Role.query.filter_by(name='READER').first()
    if not reader_role:
         # Si el rol READER no existe, falla la operación.
         # Esto debería evitarse asegurándose de que 'flask create-roles' se ejecute primero.
        return jsonify({"msg": "Error de servidor: No se encontró el rol 'READER'."}), 500

    # 3. Crear el nuevo usuario
    user = User(username=username, email=email, role_id=reader_role.id)
    user.set_password(password) # Cifra la contraseña

    # 4. Guardar en la base de datos
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar el usuario en DB: {e}")
        return jsonify({"msg": "Error al guardar el usuario. Inténtalo de nuevo."}), 500

    # 5. Generar un token JWT para iniciar sesión inmediatamente
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({
        "msg": "Usuario creado exitosamente.",
        "id": user.id,
        "username": user.username,
        "role": reader_role.name,
        "access_token": token
    }), 201

# Servicio para verificar las credenciales del usuario (para Login)
def verify_user_service(username_or_email, password):
    # Buscar usuario por username o email
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

    if user is None or not user.check_password(password):
        return jsonify({"msg": "Credenciales inválidas."}), 401

    # Generar token JWT para el usuario autenticado
    token = jwt.encode(
        {'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({
        "msg": "Inicio de sesión exitoso.",
        "id": user.id,
        "username": user.username,
        "role": user.role.name,
        "access_token": token
    }), 200