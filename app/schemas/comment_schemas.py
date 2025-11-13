from marshmallow import Schema, fields, validate, post_load
from app import ma # Asumiendo que 'ma' es tu instancia de Marshmallow

class ComentarioSchema(ma.Schema):
    """Schema para serializar y validar los Comentarios."""
    id = fields.Int(dump_only=True)
    
    # NOTA: Cambiado de 'texto' a 'contenido' para ser consistente con Post
    contenido = fields.Str(required=True, validate=validate.Length(min=5, max=500),
                           error_messages={"required": "El contenido del comentario es obligatorio."})
    
    # Campos de relaciones y metadata
    # usuario_id es 'dump_only' al deserializar porque se obtiene del JWT
    usuario_id = fields.Int(dump_only=True, attribute='usuario_id') 
    
    # post_id puede ser 'load_only' si se inyecta en la vista, pero lo dejamos
    # sin modificador para que sea flexible si la vista lo inyecta en el JSON.
    # En este caso, lo usamos principalmente en el URL, así que lo dejamos flexible.
    post_id = fields.Int(dump_only=True) 

    created_at = fields.DateTime(dump_only=True)
    
    # Campo de moderación (debe ser cargable/actualizable)
    is_visible = fields.Bool() 
    
    # Opcional: Para mostrar el username del autor
    username = fields.Str(dump_only=True, attribute='usuario.username')

    class Meta:
        # Aseguramos que solo queremos el objeto del modelo al cargar
        load_instance = True 
        
# Instancias del esquema
comentario_schema = ComentarioSchema()
comentarios_schema = ComentarioSchema(many=True)