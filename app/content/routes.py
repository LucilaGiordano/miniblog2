from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.auth.models import User, RoleEnum # <<-- CORREGIDO: Usamos RoleEnum
from .models import Post
from .schemas import post_schema, posts_schema, post_input_schema
from app.auth.decorators import require_permission
from sqlalchemy.exc import NoResultFound

# Crear el Blueprint de CONTENIDO
bp = Blueprint('content', __name__, url_prefix='/content')


# -------------------------------------------------------------------
# 1. LISTAR POSTS (Acceso público/lector)
# -------------------------------------------------------------------
@bp.route('/posts', methods=['GET'])
@jwt_required()
def list_posts():
    """Permite a cualquier usuario autenticado (READER o superior)
    listar todos los posts publicados."""
    try:
        # Obtenemos la información del usuario actual para un control más estricto
        user_id = get_jwt_identity()
        user_obj = db.session.get(User, user_id) # Usamos get()
        
        if not user_obj:
            return jsonify({"msg": "Usuario no encontrado"}), 404

        # Comprobamos el nivel de rol
        # Si el usuario es READER (ID=1), solo ve publicados
        if user_obj.role_id == RoleEnum.READER.value: # <<-- CORREGIDO
            q = db.select(Post).filter_by(status='published').order_by(Post.timestamp.desc())
        # Si el usuario es EDITOR (ID=2) o ADMIN (ID=3), ve todos
        else:
            q = db.select(Post).order_by(Post.timestamp.desc())

        posts = db.session.execute(q).scalars().all()
        
        return jsonify(posts_schema.dump(posts)), 200
    
    except Exception as e:
        # Esto captura errores de base de datos o de Marshmallow
        return jsonify({"msg": f"Error al listar posts: {str(e)}"}), 500


# -------------------------------------------------------------------
# 2. CREAR UN NUEVO POST (Sólo EDITOR o ADMIN)
# -------------------------------------------------------------------
@bp.route('/posts', methods=['POST'])
@jwt_required()
# Sólo permite crear a usuarios con rol EDITOR (ID 2) o superior (ADMIN ID 3)
@require_permission(min_role=RoleEnum.EDITOR.value) # <<-- CORREGIDO
def create_post():
    """Permite a EDITOR o ADMIN crear un nuevo post."""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # 1. Validación de entrada
    errors = post_input_schema.validate(data)
    if errors:
        # 422 Unprocessable Entity es el código estándar para errores de validación
        return jsonify({"msg": "Error de validación", "errors": errors}), 422
    
    try:
        # 2. Deserialización y creación del objeto Post
        new_post = Post(
            title=data['title'],
            body=data['body'],
            status=data['status'],
            author_id=user_id  # Asignamos el ID del usuario autenticado como autor
        )
        
        # 3. Guardar en la DB
        db.session.add(new_post)
        db.session.commit()
        
        # 4. Responder con el post recién creado (serializado)
        return jsonify(post_schema.dump(new_post)), 201 # 201 Created

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error al crear el post: {str(e)}"}), 500


# -------------------------------------------------------------------
# 3. VER DETALLE DEL POST (Acceso público/lector)
# -------------------------------------------------------------------
@bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    """Permite a cualquier usuario autenticado ver los detalles de un post.
    Si el post NO está publicado, solo su autor o un ADMIN/EDITOR puede verlo.
    """
    
    # Obtener el post
    post = db.session.get(Post, post_id)
    
    if post is None:
        return jsonify({"msg": "Post no encontrado"}), 404
        
    # Obtener la identidad del usuario y su rol
    user_id = get_jwt_identity()
    user_obj = db.session.get(User, user_id) # Usamos get()
    
    if not user_obj:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    # Control de visibilidad
    is_author = post.author_id == user_id
    # Verificamos si el rol del usuario es EDITOR o ADMIN
    is_editor_or_admin = user_obj.role_id in [RoleEnum.EDITOR.value, RoleEnum.ADMIN.value] # <<-- CORREGIDO

    # Regla: Si no está publicado, solo el autor o un EDITOR/ADMIN puede verlo.
    if post.status != 'published':
        if not is_author and not is_editor_or_admin:
            return jsonify({"msg": "Acceso denegado: El post no está publicado."}), 403

    # Si pasa las comprobaciones, serializar y devolver
    return jsonify(post_schema.dump(post)), 200


# -------------------------------------------------------------------
# 4. ACTUALIZAR UN POST (Sólo AUTOR o ADMIN)
# -------------------------------------------------------------------
@bp.route('/posts/<int:post_id>', methods=['PUT', 'PATCH'])
@jwt_required()
# Sólo permite actualizar a usuarios con rol EDITOR (ID 2) o superior (ADMIN ID 3)
@require_permission(min_role=RoleEnum.EDITOR.value) # <<-- CORREGIDO
def update_post(post_id):
    """Permite a EDITOR/ADMIN actualizar un post, pero solo si es el autor o ADMIN."""
    
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # 1. Validación de entrada
    errors = post_input_schema.validate(data)
    if errors:
        return jsonify({"msg": "Error de validación", "errors": errors}), 422
    
    # 2. Obtener el post y el usuario
    post = db.session.get(Post, post_id)
    user_obj = db.session.get(User, user_id) # Usamos get()
    
    if post is None:
        return jsonify({"msg": "Post no encontrado"}), 404
    if not user_obj:
        return jsonify({"msg": "Usuario no encontrado"}), 404 
        
    # 3. Control de Acceso Estricto (Sólo Autor o ADMIN puede editar)
    is_author = post.author_id == user_id
    is_admin = user_obj.role_id == RoleEnum.ADMIN.value # <<-- CORREGIDO
    
    if not is_author and not is_admin:
        return jsonify({"msg": "Acceso denegado: Solo el autor o un ADMIN puede editar este post."}), 403

    try:
        # 4. Aplicar cambios
        post.title = data.get('title', post.title)
        post.body = data.get('body', post.body)
        post.status = data.get('status', post.status)
        
        db.session.commit()
        
        return jsonify(post_schema.dump(post)), 200 # 200 OK

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error al actualizar el post: {str(e)}"}), 500


# -------------------------------------------------------------------
# 5. ELIMINAR UN POST (Sólo AUTOR o ADMIN)
# -------------------------------------------------------------------
@bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
# Sólo permite eliminar a usuarios con rol EDITOR (ID 2) o superior (ADMIN ID 3)
@require_permission(min_role=RoleEnum.EDITOR.value) # <<-- CORREGIDO
def delete_post(post_id):
    """Permite a EDITOR/ADMIN eliminar un post, pero solo si es el autor o ADMIN."""
    
    user_id = get_jwt_identity()
    
    # 1. Obtener el post y el usuario
    post = db.session.get(Post, post_id)
    user_obj = db.session.get(User, user_id) # Usamos get()
    
    if post is None:
        return jsonify({"msg": "Post no encontrado"}), 404
    if not user_obj:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    # 2. Control de Acceso Estricto (Sólo Autor o ADMIN puede eliminar)
    is_author = post.author_id == user_id
    is_admin = user_obj.role_id == RoleEnum.ADMIN.value # <<-- CORREGIDO
    
    if not is_author and not is_admin:
        return jsonify({"msg": "Acceso denegado: Solo el autor o un ADMIN puede eliminar este post."}), 403

    try:
        # 3. Eliminar de la DB
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({"msg": f"Post con ID {post_id} eliminado con éxito."}), 204 # 204 No Content

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error al eliminar el post: {str(e)}"}), 500