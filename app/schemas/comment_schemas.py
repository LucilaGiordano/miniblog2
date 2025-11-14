from app.models import Comentario
from app import ma

# ¡IMPORTANTE! Hemos eliminado la importación de UsuarioSchema para romper el ciclo.
# Marshmallow resolverá 'UsuarioSchema' usando la cadena.

class ComentarioSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Comentario
        # Incluimos todos los campos, incluyendo los nuevos
        fields = ('id', 'contenido', 'created_at', 'updated_at', 'post_id', 'usuario_id', 'is_visible', 'autor')
        load_instance = True
    
    # 🚨 CAMBIO CLAVE: Usamos la cadena 'UsuarioSchema' para la anidación.
    autor = ma.Nested('UsuarioSchema', only=('id', 'username'))

comentario_schema = ComentarioSchema()
comentarios_schema = ComentarioSchema(many=True)