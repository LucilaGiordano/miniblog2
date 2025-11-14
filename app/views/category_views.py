from flask.views import MethodView
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models import Category, Usuario, RoleName, category_schema, categories_schema

# Función de utilidad para verificar el rol del usuario actual
# Copiada aquí para que el archivo sea autocontenido y no dependa de post_views.py
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
        print(f"Error de JWT o autenticación: {e}")
        return False, jsonify({"msg": "Token inválido o requerido."}), 401

# ----------------------------------------------------------------------------------
# CategoryListAPI - GET (Listar Categorías) y POST (Crear Nueva Categoría)
# ----------------------------------------------------------------------------------

class CategoryListAPI(MethodView):

    # GET: Listar todas las categorías (Acceso Público)
    def get(self):
        try:
            categories = db.session.execute(db.select(Category).order_by(Category.id)).scalars().all()
            result = categories_schema.dump(categories)
            return jsonify(result), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al recuperar categorías: {e}"}), 500

    # POST: Crear una nueva categoría (Requiere ADMIN o EDITOR)
    @jwt_required()
    def post(self):
        # 1. Verificar Permisos
        allowed_roles = [RoleName.ADMIN.value, RoleName.EDITOR.value]
        is_ok, _, status_code = is_allowed(allowed_roles)
        
        if not is_ok:
            return _, status_code # Devuelve el error de permiso (403) o autenticación (401)

        json_data = request.get_json()
        
        # 2. Deserializar/Validar la entrada con Marshmallow
        try:
            # Usamos load para validar los datos
            category_data = category_schema.load(json_data)
        except Exception as err:
            return jsonify(err.messages), 400

        # 3. Crear el nuevo objeto Category
        new_category = Category(
            name=category_data.get('name'),
            description=category_data.get('description')
        )

        try:
            db.session.add(new_category)
            db.session.commit()
            # 4. Serializar la respuesta
            return category_schema.jsonify(new_category), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"msg": "Error de integridad: Ya existe una categoría con ese nombre."}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al crear la categoría: {e}"}), 500


# ----------------------------------------------------------------------------------
# CategoryDetailAPI - GET (Categoría por ID), PUT (Editar Categoría), DELETE (Eliminar Categoría)
# ----------------------------------------------------------------------------------

class CategoryDetailAPI(MethodView):

    # GET: Obtener una categoría específica (Acceso Público)
    def get(self, category_id):
        category = db.session.get(Category, category_id)
        if category is None:
            return jsonify({"msg": "Categoría no encontrada"}), 404
        
        # Serializar y devolver la categoría
        return category_schema.jsonify(category), 200

    # PUT: Editar una categoría (Requiere ADMIN o EDITOR)
    @jwt_required()
    def put(self, category_id):
        # 1. Verificar Permisos
        allowed_roles = [RoleName.ADMIN.value, RoleName.EDITOR.value]
        is_ok, _, status_code = is_allowed(allowed_roles)
        
        if not is_ok:
            return _, status_code # Devuelve el error de permiso (403) o autenticación (401)

        # 2. Obtener la Categoría
        category = db.session.get(Category, category_id)
        if category is None:
            return jsonify({"msg": "Categoría no encontrada"}), 404

        json_data = request.get_json()
        
        # 3. Deserializar/Validar la entrada con Marshmallow
        try:
            # Usamos partial=True para permitir la actualización parcial de campos
            category_data = category_schema.load(json_data, partial=True)
        except Exception as err:
            return jsonify(err.messages), 400

        # 4. Actualizar el objeto Category
        category.name = category_data.get('name', category.name)
        category.description = category_data.get('description', category.description)

        try:
            db.session.commit()
            # 5. Serializar la respuesta
            return category_schema.jsonify(category), 200
        except IntegrityError:
            db.session.rollback()
            return jsonify({"msg": "Error de integridad: Ya existe una categoría con ese nombre."}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al actualizar la categoría: {e}"}), 500

    # DELETE: Eliminar una categoría (Requiere ADMIN o EDITOR)
    @jwt_required()
    def delete(self, category_id):
        # 1. Verificar Permisos
        allowed_roles = [RoleName.ADMIN.value, RoleName.EDITOR.value]
        is_ok, _, status_code = is_allowed(allowed_roles)
        
        if not is_ok:
            return _, status_code # Devuelve el error de permiso (403) o autenticación (401)

        # 2. Obtener la Categoría
        category = db.session.get(Category, category_id)
        if category is None:
            return jsonify({"msg": "Categoría no encontrada"}), 404

        # Comprobación adicional: No se puede eliminar una categoría si tiene posts asociados (buena práctica de BD)
        if category.posts.count() > 0:
            return jsonify({"msg": "No se puede eliminar la categoría. Primero elimina los posts asociados."}), 409
        
        try:
            db.session.delete(category)
            db.session.commit()
            return jsonify({"msg": "Categoría eliminada exitosamente"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": f"Error al eliminar la categoría: {e}"}), 500