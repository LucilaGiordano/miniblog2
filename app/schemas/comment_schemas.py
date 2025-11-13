from app import ma
from marshmallow import fields, validate

class ComentarioSchema(ma.Schema):
    """Schema para serializar y validar los Comentarios."""
    id = fields.Int(dump_only=True)
    
    texto = fields.Str(required=True, validate=validate.Length(min=5))
    
    # Campos de relaciones y metadata
    autor_id = fields.Int(dump_only=True, attribute='usuario_id')
    post_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True, attribute='created_at')
    
    # Campo de moderación
    is_visible = fields.Bool() 
    
    class Meta:
        load_instance = True