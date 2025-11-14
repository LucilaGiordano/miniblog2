from flask.views import MethodView
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models import Post, Usuario, Category, RoleName, post_schema, posts_schema

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


# ----------------------------------------------------------------------------------
# PostListAPI - GET (Listar Posts) y POST (Crear Nuevo Post)
# ----------------------------------------------------------------------------------

class PostListAPI(MethodView):

    # GET: Listar todos los posts (Acceso Público)
    def get(self):
        try:
            # Ordenamos por timestamp descendente (los más nuevos primero)
            posts = db.session.execute(db.select(Post).order_by(Post.timestamp.desc())).scalars().all()
            result = posts_schema.dump(posts)
            return jsonify(result), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al recuperar posts: {e}"}), 500

    # POST: Crear un nuevo post (Requiere ADMIN o EDITOR)
    @jwt_required()
    def post(self):
        # 1. Verificar Permisos
        # Solo ADMIN y EDITOR pueden crear posts
        allowed_roles = [RoleName.ADMIN.value, RoleName.EDITOR.value]
        is_ok, current_user, status_code = is_allowed(allowed_roles)
        
        if not is_ok:
            # is_ok es False, devolvemos la respuesta de error y el código de estado
            return current_user, status_code 

        json_data = request.get_json()
        
        # 2. Deserializar/Validar la entrada con Marshmallow
        try:
            # Los campos user_id y category_id se esperan en la carga (load)
            post_data = post_schema.load(json_data)
        except Exception as err:
            return jsonify(err.messages), 400

        # 3. Verificar que la categoría existe (Importante para la integridad)
        category_id = post_data.get('category_id')
        category = db.session.get(Category, category_id)
        if category is None:
            return jsonify({"msg": f"La categoría con ID {category_id} no existe."}), 400

        # 4. Crear el nuevo objeto Post
        new_post = Post(
            title=post_data.get('title'),
            body=post_data.get('body'),
            user_id=current_user.id, # El autor siempre es el usuario autenticado
            category_id=category_id
        )

        try:
            db.session.add(new_post)
            db.session.commit()
            # 5. Serializar la respuesta
            return post_schema.jsonify(new_post), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al crear el post: {e}"}), 500


# ----------------------------------------------------------------------------------
# PostDetailAPI - GET (Post por ID), PUT (Editar Post), DELETE (Eliminar Post)
# ----------------------------------------------------------------------------------

class PostDetailAPI(MethodView):

    # GET: Obtener un post específico (Acceso Público)
    def get(self, post_id):
        post = db.session.get(Post, post_id)
        if post is None:
            return jsonify({"msg": "Post no encontrado"}), 404
        
        # Serializar y devolver el post
        return post_schema.jsonify(post), 200

    # PUT: Editar un post (Requiere ADMIN o ser el autor)
    @jwt_required()
    def put(self, post_id):
        # 1. Obtener el Post
        post = db.session.get(Post, post_id)
        if post is None:
            return jsonify({"msg": "Post no encontrado"}), 404

        # 2. Verificar Permisos (Admin o Autor)
        allowed_roles = [RoleName.ADMIN.value] # Solo ADMIN tiene permiso absoluto para editar cualquier post
        is_admin_ok, user_or_response, status_code = is_allowed(allowed_roles)

        if not is_admin_ok:
            # Si no es ADMIN, comprobamos si es el autor del post
            current_user_id = get_jwt_identity()
            if post.user_id != current_user_id:
                # El usuario no es ADMIN ni el autor
                return jsonify({"msg": "Acceso denegado. Solo el autor del post o un ADMIN pueden editarlo."}), 403
            
        # Si llegamos aquí, es ADMIN o el AUTOR.

        json_data = request.get_json()
        
        # 3. Deserializar/Validar la entrada con Marshmallow
        try:
            # Usamos partial=True para permitir la actualización parcial de campos
            post_data = post_schema.load(json_data, partial=True)
        except Exception as err:
            return jsonify(err.messages), 400

        # 4. Verificar que la nueva categoría (si se proporciona) existe
        category_id = post_data.get('category_id')
        if category_id is not None:
            category = db.session.get(Category, category_id)
            if category is None:
                return jsonify({"msg": f"La categoría con ID {category_id} no existe."}), 400

        # 5. Actualizar el objeto Post
        post.title = post_data.get('title', post.title)
        post.body = post_data.get('body', post.body)
        post.category_id = category_id if category_id is not None else post.category_id

        try:
            db.session.commit()
            # 6. Serializar la respuesta
            return post_schema.jsonify(post), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al actualizar el post: {e}"}), 500

    # DELETE: Eliminar un post (Requiere ADMIN o ser el autor)
    @jwt_required()
    def delete(self, post_id):
        # 1. Obtener el Post
        post = db.session.get(Post, post_id)
        if post is None:
            return jsonify({"msg": "Post no encontrado"}), 404

        # 2. Verificar Permisos (Admin o Autor)
        allowed_roles = [RoleName.ADMIN.value] # Solo ADMIN tiene permiso absoluto para eliminar cualquier post
        is_admin_ok, user_or_response, status_code = is_allowed(allowed_roles)

        if not is_admin_ok:
            # Si no es ADMIN, comprobamos si es el autor del post
            current_user_id = get_jwt_identity()
            if post.user_id != current_user_id:
                # El usuario no es ADMIN ni el autor
                return jsonify({"msg": "Acceso denegado. Solo el autor del post o un ADMIN pueden eliminarlo."}), 403

        # Si llegamos aquí, es ADMIN o el AUTOR.

        try:
            # Debido a 'cascade="all, delete-orphan"' en Comment, los comentarios
            # asociados se eliminarán automáticamente.
            db.session.delete(post)
            db.session.commit()
            return jsonify({"msg": "Post eliminado exitosamente"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al eliminar el post: {e}"}), 500