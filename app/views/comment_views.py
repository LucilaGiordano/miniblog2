from flask.views import MethodView
from flask import request, jsonify
from app import db # Asume que 'db' es tu instancia de SQLAlchemy
from ..models import Comentario, Post
from ..schemas.comment_schemas import ComentarioSchema
from ..decorators.auth_decorators import check_ownership # ✅ CORRECCIÓN RELATIVA
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt # Se necesita get_jwt para el rol
from sqlalchemy.orm.exc import NoResultFound

# Instanciamos los schemas
comentario_schema = ComentarioSchema()
comentarios_schema = ComentarioSchema(many=True)

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
        
        # 2. Obtener solo comentarios visibles y ordenar por fecha
        comentarios = Comentario.query.filter_by(
            post_id=post_id, 
            is_visible=True
        ).order_by(Comentario.created_at.desc()).all()
        
        return jsonify(comentarios_schema.dump(comentarios)), 200

    # Endpoint privado: Crear un nuevo comentario
    @jwt_required()
    def post(self, post_id):
        # 🛑 CORRECCIÓN CLAVE: Convertir la identidad (string) a int antes de usarla como FK.
        user_id = int(get_jwt_identity())
        
        # 1. Validar si el Post existe
        post = Post.query.get(post_id)
        if not post:
            return jsonify({"msg": "No se puede comentar: Post no encontrado."}), 404
            
        # 2. Validar los datos de entrada (solo necesitamos 'texto')
        data = request.json
        try:
            validated_data = comentario_schema.load(data)
        except Exception as e:
            return jsonify({"errors": str(e)}), 400
        
        # 3. Crear el Comentario
        new_comment = Comentario(
            texto=validated_data['texto'],
            usuario_id=user_id, # Usamos el ID convertido a int
            post_id=post_id
        )

        db.session.add(new_comment)
        try:
            db.session.commit()
            return jsonify({
                "msg": "Comentario agregado exitosamente y pendiente de aprobación (si aplica).",
                "comentario": comentario_schema.dump(new_comment)
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al guardar el comentario.", "details": str(e)}), 500


class CommentDetailAPI(MethodView):
    """
    Maneja PUT (editar) y DELETE (eliminar) de un comentario específico.
    Ruta: /api/comments/<int:comment_id>
    """

    # Endpoint privado: Editar un comentario (Solo autor o admin)
    @jwt_required()
    def put(self, comment_id):
        comentario = Comentario.query.get_or_404(comment_id)
        
        # 1. Verificar propiedad (autor o admin)
        if not check_ownership(comentario.usuario_id):
            return jsonify({"msg": "Acceso denegado. No eres el autor de este comentario ni administrador."}), 403

        # 2. Validar los datos de entrada (permitimos actualización parcial)
        data = request.json
        try:
            validated_data = comentario_schema.load(data, partial=True)
        except Exception as e:
            return jsonify({"errors": str(e)}), 400

        # 3. Actualizar campos
        comentario.texto = validated_data.get('texto', comentario.texto)
        
        # El campo is_visible puede ser modificado por un admin/moderador
        # Necesitamos el rol del usuario actual
        user_claims = get_jwt()
        
        if 'is_visible' in validated_data and user_claims.get('role') in ['admin', 'moderator']:
            comentario.is_visible = validated_data['is_visible']
        # Si no es admin/moderator, no puede cambiar is_visible
        elif 'is_visible' in validated_data and user_claims.get('role') == 'user':
            # Solo permitir a un usuario cambiar la visibilidad si el comentario es suyo
            if check_ownership(comentario.usuario_id):
                comentario.is_visible = validated_data['is_visible']
            else:
                return jsonify({"msg": "No tienes permiso para modificar el estado de visibilidad de este comentario."}), 403


        # 4. Guardar cambios en la DB
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
    def delete(self, comment_id):
        comentario = Comentario.query.get_or_404(comment_id)
        
        # 1. Verificar propiedad (autor o admin)
        if not check_ownership(comentario.usuario_id):
            return jsonify({"msg": "Acceso denegado. No eres el autor de este comentario ni administrador."}), 403

        db.session.delete(comentario)
        try:
            db.session.commit()
            return jsonify({"msg": f"Comentario ID {comment_id} eliminado exitosamente."}), 204
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al eliminar el comentario.", "details": str(e)}), 500