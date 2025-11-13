from functools import wraps
from flask import abort, jsonify
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity

# --- Decorador de Verificación de Roles ---

def roles_required(*roles):
    """
    Decorador personalizado que verifica si el usuario autenticado tiene uno de los roles permitidos.
    Debe ser usado después de @jwt_required().
    
    Ejemplo: @roles_required("admin", "moderator")
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Requiere que el JWT haya sido validado previamente.
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role not in roles:
                # 403 Forbidden: No tiene permiso. Devolvemos JSON.
                return jsonify(
                    msg="Acceso denegado. Rol insuficiente.", 
                    required_roles=roles,
                    user_role=user_role
                ), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# --- Función de Verificación de Propiedad ---

def check_ownership(resource_owner_id):
    """
    Verifica si el usuario actual es el dueño del recurso. 
    Permite acceso total si el rol es 'admin'.
    
    :param resource_owner_id: ID del usuario que creó el recurso (Post o Comentario).
    :return: True si es dueño o admin, False en caso contrario.
    """
    # 1. Obtener los datos del token
    claims = get_jwt()
    
    # 🛑 CORRECCIÓN CLAVE: El identity de JWT es un string. Lo convertimos a int para compararlo
    # con el ID del recurso (que es int) y evitar el error "Subject must be a string"
    current_user_id = int(get_jwt_identity()) 

    # 2. El administrador siempre puede realizar la operación
    if claims.get('role') == 'admin':
        return True
    
    # 3. El usuario puede modificar/eliminar si es el dueño del recurso
    # Aseguramos que ambos IDs sean integers antes de comparar
    return current_user_id == int(resource_owner_id)