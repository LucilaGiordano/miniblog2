from flask.views import MethodView
from flask import request, jsonify
from .. import db  # Asume que 'db' es tu instancia de SQLAlchemy
from ..models import Usuario, Role, RoleName  # AÑADIDO: Importamos Role y RoleName
from ..models import usuario_schema, usuarios_schema  # Usamos los schemas del models.py
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import datetime

# Instanciamos los schemas de DUMP (mostrar datos)
usuario_dump_schema = usuario_schema
usuarios_dump_schema = usuarios_schema

# Función de utilidad para verificar el rol del usuario actual
def is_allowed(allowed_roles):
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        current_user = db.session.get(Usuario, user_id)
        
        if not current_user:
            return False, jsonify({"msg": "Usuario no encontrado."}), 404

        user_role_name = current_user.role.name.value
        
        if user_role_name in allowed_roles:
            return True, current_user, None
        else:
            return False, jsonify({"msg": "Acceso denegado. Rol insuficiente."}), 403
            
    except Exception as e:
        return False, jsonify({"msg": "Token inválido o requerido."}), 401


class RegisterAPI(MethodView):
    def post(self):
        data = request.json
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"errors": "Faltan campos obligatorios: username, email y password."}), 400

        if db.session.execute(db.select(Usuario).filter_by(username=username)).scalar_one_or_none() or \
           db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one_or_none():
            return jsonify({"msg": "El nombre de usuario o email ya están registrados."}), 409

        default_role = db.session.execute(
            db.select(Role)
            .where(Role.name == RoleName.READER)
        ).scalar_one_or_none()
        
        if not default_role:
            return jsonify({"error": "Error de configuración: Rol 'reader' no encontrado."}), 500

        new_user = Usuario(
            username=username,
            email=email,
            role=default_role
        )
        
        new_user.set_password(password)

        db.session.add(new_user)
        try:
            db.session.commit()
            return jsonify({"msg": f"Usuario {new_user.username} registrado exitosamente con rol '{new_user.role.name.value}'. Por favor, inicie sesión."}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al registrar el usuario.", "details": str(e)}), 500


class LoginAPI(MethodView):
    """
    Maneja el inicio de sesión y la generación de JWT.
    """
    def post(self):
        data = request.json
        
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"errors": "Faltan campos obligatorios: email y password."}), 400

        user = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one_or_none()
        
        if user is None:
            return jsonify({"msg": "Credenciales inválidas (email no encontrado)."}), 401

        if not user.check_password(password):
            return jsonify({"msg": "Credenciales inválidas (contraseña incorrecta)."}), 401

        # 🔥🔥🔥 ACÁ ESTÁ LO QUE VOS PEDISTE — TOKEN CON EMAIL INCLUIDO 🔥🔥🔥
        try:
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    'role': user.role.name.value,
                    'email': user.email    # ⬅️ AGREGADO AHORA
                },
                expires_delta=datetime.timedelta(hours=24)
            )
        except Exception as e:
            return jsonify({"error": "Fallo al crear el token de acceso.", "details": str(e)}), 500

        return jsonify({
            "access_token": access_token,
            "msg": "Inicio de sesión exitoso.",
            "user": usuario_dump_schema.dump(user)
        }), 200


class UserDetailAPI(MethodView):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = db.session.get(Usuario, user_id)
        
        if user is None:
            return jsonify({"msg": "Usuario no encontrado, ID del token inválido."}), 404
        
        return jsonify(usuario_dump_schema.dump(user)), 200


class UserListAPI(MethodView):
    @jwt_required()
    def get(self):
        allowed_roles = [RoleName.ADMIN.value]
        is_ok, user_or_response, status_code = is_allowed(allowed_roles)
        
        if not is_ok:
            return user_or_response, status_code

        try:
            users = db.session.execute(db.select(Usuario).order_by(Usuario.username)).scalars().all()
            result = usuarios_dump_schema.dump(users)
            return jsonify(result), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al recuperar usuarios: {e}"}), 500
