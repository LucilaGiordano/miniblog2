from flask.views import MethodView
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models import Comment, Post, Usuario, RoleName, comment_schema, comments_schema

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
        # Errores de JWT (token expirado, inválido, etc.)
        return False, jsonify({"msg": "Token inválido o requerido."}), 401


# ----------------------------------------------------------------------------------
# CommentListAPI - GET (Listar Comentarios por Post) y POST (Crear Nuevo Comentario)
# ----------------------------------------------------------------------------------

class CommentListAPI(MethodView):

    # GET: Listar comentarios para un post específico (Acceso Público)
    def get(self, post_id):
        post = db.session.get(Post, post_id)
        if post is None:
            return jsonify({"msg": "Post no encontrado"}), 404
        
        # Filtramos los comentarios por el post_id
        comments = db.session.execute(
            db.select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.timestamp.asc())
        ).scalars().all()
        
        result = comments_schema.dump(comments)
        return jsonify(result), 200

    # POST: Crear un nuevo comentario (Requiere cualquier usuario autenticado)
    @jwt_required()
    def post(self, post_id):
        # 1. Verificar si el post existe
        post = db.session.get(Post, post_id)
        if post is None:
            return jsonify({"msg": "Post no encontrado"}), 404

        # 2. El usuario debe estar autenticado (jwt_required ya lo asegura)
        user_id = get_jwt_identity()
        current_user = db.session.get(Usuario, user_id)
        
        if not current_user:
            return jsonify({"msg": "Error de autenticación. Usuario no identificado."}), 401
        
        json_data = request.get_json()
        
        # 3. Deserializar/Validar la entrada con Marshmallow
        try:
            # Solo necesitamos el cuerpo del comentario (body)
            comment_data = comment_schema.load(json_data, partial=True)
        except Exception as err:
            return jsonify(err.messages), 400

        # 4. Crear el nuevo objeto Comment
        new_comment = Comment(
            body=comment_data.get('body'),
            user_id=current_user.id, # Autor del comentario
            post_id=post_id          # Post al que pertenece
        )

        try:
            db.session.add(new_comment)
            db.session.commit()
            # 5. Serializar la respuesta
            return comment_schema.jsonify(new_comment), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al crear el comentario: {e}"}), 500


# ----------------------------------------------------------------------------------
# CommentDetailAPI - PUT (Editar Comentario) y DELETE (Eliminar Comentario)
# ----------------------------------------------------------------------------------

class CommentDetailAPI(MethodView):

    # PUT: Editar un comentario (Requiere ADMIN o ser el autor)
    @jwt_required()
    def put(self, post_id, comment_id):
        # 1. Obtener el Comentario
        comment = db.session.get(Comment, comment_id)
        if comment is None:
            return jsonify({"msg": "Comentario no encontrado"}), 404
        
        # 2. Verificar que el comentario pertenece al post_id (coherencia de URL)
        if comment.post_id != post_id:
            return jsonify({"msg": "El comentario no pertenece a este post."}), 404

        # 3. Verificar Permisos (Admin o Autor)
        allowed_roles = [RoleName.ADMIN.value] # Solo ADMIN tiene permiso absoluto
        is_admin_ok, user_or_response, status_code = is_allowed(allowed_roles)

        if not is_admin_ok:
            # Si no es ADMIN, comprobamos si es el autor del comentario
            current_user_id = get_jwt_identity()
            if comment.user_id != current_user_id:
                # El usuario no es ADMIN ni el autor
                return jsonify({"msg": "Acceso denegado. Solo el autor del comentario o un ADMIN pueden editarlo."}), 403
            
        # Si llegamos aquí, es ADMIN o el AUTOR.

        json_data = request.get_json()
        
        # 4. Deserializar/Validar la entrada con Marshmallow
        try:
            comment_data = comment_schema.load(json_data, partial=True)
        except Exception as err:
            return jsonify(err.messages), 400

        # 5. Actualizar el objeto Comment
        comment.body = comment_data.get('body', comment.body)
        
        try:
            db.session.commit()
            # 6. Serializar la respuesta
            return comment_schema.jsonify(comment), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al actualizar el comentario: {e}"}), 500

    # DELETE: Eliminar un comentario (Requiere ADMIN o ser el autor)
    @jwt_required()
    def delete(self, post_id, comment_id):
        # 1. Obtener el Comentario
        comment = db.session.get(Comment, comment_id)
        if comment is None:
            return jsonify({"msg": "Comentario no encontrado"}), 404
        
        # 2. Verificar que el comentario pertenece al post_id (coherencia de URL)
        if comment.post_id != post_id:
            return jsonify({"msg": "El comentario no pertenece a este post."}), 404

        # 3. Verificar Permisos (Admin o Autor)
        allowed_roles = [RoleName.ADMIN.value] # Solo ADMIN tiene permiso absoluto
        is_admin_ok, user_or_response, status_code = is_allowed(allowed_roles)

        if not is_admin_ok:
            # Si no es ADMIN, comprobamos si es el autor del comentario
            current_user_id = get_jwt_identity()
            if comment.user_id != current_user_id:
                # El usuario no es ADMIN ni el autor
                return jsonify({"msg": "Acceso denegado. Solo el autor del comentario o un ADMIN pueden eliminarlo."}), 403

        # Si llegamos aquí, es ADMIN o el AUTOR.

        try:
            db.session.delete(comment)
            db.session.commit()
            return jsonify({"msg": "Comentario eliminado exitosamente"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al eliminar el comentario: {e}"}), 500