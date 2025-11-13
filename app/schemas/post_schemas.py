from app import ma
from marshmallow import fields, validate

# Importamos el schema de Categoría para anidarlo
# ✅ CORRECCIÓN: Usamos importación relativa para asegurarnos de que funcione dentro del paquete 'app'.
from .category_schemas import CategoriaSchema 

class PostSchema(ma.Schema):
    """Schema para serializar y validar los Posts, incluyendo Categorías."""
    id = fields.Int(dump_only=True)
    
    # Campos requeridos
    titulo = fields.Str(required=True, validate=validate.Length(min=5, max=120))
    contenido = fields.Str(required=True, validate=validate.Length(min=10))
    
    # Campo para recibir las CATEGORIAS (lista de IDs al cargar/validar)
    # Lista de enteros (IDs) que se usa para crear/actualizar el post
    categoria_ids = fields.List(fields.Int(), load_only=True, required=False)

    # Campo para mostrar las CATEGORIAS (serializar)
    # Usamos CategoriaSchema para anidar la data de categorías en la respuesta GET
    categorias = fields.List(fields.Nested(CategoriaSchema(only=('id', 'nombre'))), dump_only=True)
    
    # Campos de relaciones y metadata (solo lectura al enviar datos)
    autor_id = fields.Int(dump_only=True, attribute='usuario_id')
    created_at = fields.DateTime(dump_only=True, attribute='created_at')
    updated_at = fields.DateTime(dump_only=True, attribute='updated_at')
    is_published = fields.Bool()
    
    class Meta:
        load_instance = True