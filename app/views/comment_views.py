from flask.views import MethodView
from flask import request, jsonify
from app import db 
from ...models import Comentario, Post
# Importamos las instancias del esquema corregido
from ..schemas.comment_schemas import comentario_schema, comentarios_schema 
from ...decorators.auth_decorators import check_ownership # Usamos el decorador de verificación
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt # get_jwt para el rol

class CommentListAPI(MethodView):
    """
    Maneja GET (lista de comentarios de un post) y POST (crear nuevo comentario).
    Ruta: /api/posts/<int:post_id>/comments
    """

    # Endpoint público: Obtener todos los comentarios de un post
    def get(self, post_id):
        # 1. Verificar si el Post existe y está publicado
        post = Post.query.filter_by(id=post_id, is_published=True).first()
        if not post:
            return jsonify({"msg": "Post no encontrado o no publicado."}), 404
        
        # 2. Obtener solo comentarios visibles y ordenar por fecha (ascendente para el hilo)
        comentarios = Comentario.query.filter_by(
            post_id=post_id, 
            is_visible=True
        ).order_by(Comentario.created_at.asc()).all() 
        
        return jsonify(comentarios_schema.dump(comentarios)), 200

    # Endpoint privado: Crear un nuevo comentario
    @jwt_required()
    def post(self, post_id):
        # Obtener ID de usuario del token
        user_id = int(get_jwt_identity())
        
        # 1. Validar si el Post existe
        post = Post.query.get(post_id)
        if not post:
            return jsonify({"msg": "No se puede comentar: Post no encontrado."}), 404
            
        # 2. Validar los datos de entrada (se espera 'contenido')
        data = request.json
        try:
            validated_data = comentario_schema.load(data) 
        except Exception as e:
            return jsonify({"errors": str(e)}), 400
        
        # 3. Crear el Comentario
        new_comment = Comentario(
            contenido=validated_data['contenido'], # Usa 'contenido'
            usuario_id=user_id, 
            post_id=post_id
        )
        # Nota: Asumimos que el modelo asigna is_visible=True o el valor por defecto

        db.session.add(new_comment)
        try:
            db.session.commit()
            return jsonify({
                "msg": "Comentario agregado exitosamente.",
                "comentario": comentario_schema.dump(new_comment)
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al guardar el comentario.", "details": str(e)}), 500


class CommentDetailAPI(MethodView):
    """
    Maneja PUT (editar) y DELETE (eliminar) de un comentario específico.
    Ruta: /api/posts/<int:post_id>/comments/<int:comment_id>
    """

    # Endpoint privado: Editar un comentario (Solo autor o admin)
    @jwt_required()
    def put(self, post_id, comment_id):
        # 1. Buscar el comentario y verificar que pertenezca al post_id
        # 🚨 CAMBIO CLAVE: Filtra por ambos IDs para el ruteo anidado
        comentario = Comentario.query.filter_by(id=comment_id, post_id=post_id).first()
        
        if not comentario:
            return jsonify({"msg": "Comentario no encontrado o no pertenece a este post."}), 404

        # 2. Verificar propiedad (autor o admin/moderador)
        if not check_ownership(comentario.usuario_id):
            return jsonify({"msg": "Acceso denegado. No eres el autor de este comentario ni administrador/moderador."}), 403

        # 3. Validar los datos de entrada
        data = request.json
        try:
            validated_data = comentario_schema.load(data, partial=True)
        except Exception as e:
            return jsonify({"errors": str(e)}), 400

        # 4. Actualizar campos
        comentario.contenido = validated_data.get('contenido', comentario.contenido) # Usa 'contenido'
        
        # 5. Manejar la moderación de 'is_visible'
        user_claims = get_jwt()
        
        if 'is_visible' in validated_data:
            # Solo permitir cambiar visibilidad si es admin/moderator
            if user_claims.get('role') in ['admin', 'moderator']:
                comentario.is_visible = validated_data['is_visible']
            else:
                return jsonify({"msg": "No tienes permiso para modificar el estado de visibilidad."}), 403

        # 6. Guardar cambios en la DB
        try:
            db.session.commit()
            return jsonify({
                "msg": "Comentario actualizado exitosamente.",
                "comentario": comentario_schema.dump(comentario)
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al actualizar el comentario.", "details": str(e)}), 500

    # Endpoint privado: Eliminar un comentario (Solo autor o admin)
    @jwt_required()
    def delete(self, post_id, comment_id):
        # 1. Buscar el comentario y verificar que pertenezca al post_id
        # 🚨 CAMBIO CLAVE: Filtra por ambos IDs para el ruteo anidado
        comentario = Comentario.query.filter_by(id=comment_id, post_id=post_id).first()

        if not comentario:
            return jsonify({"msg": "Comentario no encontrado o no pertenece a este post."}), 404
        
        # 2. Verificar propiedad (autor o admin)
        if not check_ownership(comentario.usuario_id):
            return jsonify({"msg": "Acceso denegado. No eres el autor de este comentario ni administrador."}), 403

        db.session.delete(comentario)
        try:
            db.session.commit()
            return jsonify({"msg": f"Comentario ID {comment_id} eliminado exitosamente."}), 204
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al eliminar el comentario.", "details": str(e)}), 500