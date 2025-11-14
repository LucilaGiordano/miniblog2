from flask.views import MethodView
from flask import request, jsonify
from .. import db # Asume que 'db' es tu instancia de SQLAlchemy
from ..models import Usuario, Role, RoleName # AÑADIDO: Importamos Role y RoleName
from ..models import usuario_schema, usuarios_schema # Usamos los schemas del models.py
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import datetime

# Instanciamos los schemas de DUMP (mostrar datos)
# Nota: Ahora usamos los schemas de Marshmallow que definiste en models.py
usuario_dump_schema = usuario_schema
usuarios_dump_schema = usuarios_schema

# Función de utilidad para verificar el rol del usuario actual
def is_allowed(allowed_roles):
    """
    Verifica si el usuario autenticado tiene uno de los roles permitidos.
    Retorna (True, current_user, None) si el rol es suficiente.
    Retorna (False, response, status_code) si falla la autenticación o la autorización.
    """
    try:
        # Asegura que haya un token JWT válido
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        current_user = db.session.get(Usuario, user_id)
        
        if not current_user:
            return False, jsonify({"msg": "Usuario no encontrado."}), 404

        # Obtener el nombre del rol del usuario (Ej: 'admin', 'editor', 'reader')
        user_role_name = current_user.role.name.value
        
        if user_role_name in allowed_roles:
            return True, current_user, None
        else:
            return False, jsonify({"msg": "Acceso denegado. Rol insuficiente."}), 403
            
    except Exception as e:
        # Maneja errores de JWT (token expirado, inválido, etc.)
        return False, jsonify({"msg": "Token inválido o requerido."}), 401

class RegisterAPI(MethodView):
    """
    Maneja el registro de nuevos usuarios, asignando automáticamente el rol READER.
    """
    def post(self):
        data = request.json
        
        # 1. Validar datos de entrada usando el esquema de Usuario (se asume que existe un esquema de carga)
        try:
            # Usamos el esquema de Usuario para cargar los campos necesarios (username, email, password)
            # Como no tenemos un RegisterSchema en el archivo de modelos anterior, usamos un diccionario simple.
            # En una aplicación real, usarías el RegisterSchema. Aquí asumimos que recibes username, email y password.
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username or not email or not password:
                 return jsonify({"errors": "Faltan campos obligatorios: username, email y password."}), 400

        except Exception as e:
            return jsonify({"errors": str(e)}), 400 # Error de validación o formato

        # 2. Verificar existencia
        if db.session.execute(db.select(Usuario).filter_by(username=username)).scalar_one_or_none() or \
           db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one_or_none():
            return jsonify({"msg": "El nombre de usuario o email ya están registrados."}), 409

        # 3. Obtener el objeto Role por defecto (RoleName.READER)
        # Buscamos el objeto Role donde el nombre sea 'reader'
        default_role = db.session.execute(
            db.select(Role)
            .where(Role.name == RoleName.READER)
        ).scalar_one_or_none()
        
        if not default_role:
             # Este es un error de configuración de DB, el rol 'reader' debe existir.
             return jsonify({"error": "Error de configuración: Rol 'reader' no encontrado."}), 500


        # 4. Crear usuario
        new_user = Usuario(
            username=username,
            email=email,
            # ASIGNACIÓN CLAVE: Usamos el objeto default_role
            role=default_role 
        )
        
        # Hashear y asignar contraseña
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
        
        # 1. Validar datos de entrada (asumiendo email y password)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
             return jsonify({"errors": "Faltan campos obligatorios: email y password."}), 400

        # 2. Buscar usuario
        user = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar_one_or_none()
        
        if user is None:
            return jsonify({"msg": "Credenciales inválidas (email no encontrado)."}), 401

        # 3. Verificar la contraseña
        if not user.check_password(password):
            return jsonify({"msg": "Credenciales inválidas (contraseña incorrecta)."}), 401

        # 4. Crear el Token de Acceso
        try:
            # Incluimos el nombre del rol en las claims adicionales para facilitar la verificación en el frontend
            access_token = create_access_token(
                identity=user.id, 
                additional_claims={'role': user.role.name.value}, # AÑADIDO: Incluir el nombre del rol
                expires_delta=datetime.timedelta(hours=24)
            )
        except Exception as e:
            return jsonify({"error": "Fallo al crear el token de acceso.", "details": str(e)}), 500

        # 5. Respuesta exitosa
        return jsonify({
            "access_token": access_token,
            "msg": "Inicio de sesión exitoso.",
            "user": usuario_dump_schema.dump(user) # Serializa el objeto Usuario
        }), 200


class UserDetailAPI(MethodView):
    """
    Maneja GET (detalle de usuario actual).
    """
    @jwt_required()
    def get(self):
        # Obtiene la identity (que es el ID de usuario) del token
        user_id = get_jwt_identity() 
        
        user = db.session.get(Usuario, user_id)
        
        if user is None:
            return jsonify({"msg": "Usuario no encontrado, ID del token inválido."}), 404
        
        return jsonify(usuario_dump_schema.dump(user)), 200


class UserListAPI(MethodView):
    """
    Maneja GET (Listado de todos los usuarios).
    ACCESO RESTRINGIDO: Solo para ADMIN.
    """
    @jwt_required()
    def get(self):
        # 1. Verificar Permisos (Solo ADMIN)
        allowed_roles = [RoleName.ADMIN.value]
        is_ok, user_or_response, status_code = is_allowed(allowed_roles)
        
        if not is_ok:
            return user_or_response, status_code

        # 2. Recuperar todos los usuarios
        try:
            users = db.session.execute(db.select(Usuario).order_by(Usuario.username)).scalars().all()
            result = usuarios_dump_schema.dump(users)
            return jsonify(result), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al recuperar usuarios: {e}"}), 500