from marshmallow import fields, validate
# Importamos la instancia de Marshmallow (ma)
from app.extensions import ma 
# Importamos el modelo de la tabla que vamos a serializar
from .models import Post 
# Necesitamos el modelo User para el campo del autor
from app.auth.models import User 

# --- Esquema para serializar la información básica del Autor ---
# Se usará para incrustar el nombre del autor en el PostSchema.
class EmbeddedUserSchema(ma.SQLAlchemySchema):
    """Esquema para la serialización básica del autor dentro del Post."""
    class Meta:
        model = User
        fields = ("id", "username")

# --- Esquema Principal para el Modelo Post ---
class PostSchema(ma.SQLAlchemySchema):
    """Esquema para serializar/deserializar el modelo Post."""
    class Meta:
        model = Post
        # Campos que se mostrarán al serializar un objeto Post
        fields = (
            "id", 
            "title", 
            "body", 
            "status", 
            "timestamp", 
            "last_edited", 
            "author_id", 
            "author"
        )
        # Permite la carga de datos del modelo, importante para el CRUD
        load_instance = True 
        
    # Relación de anidación: incluye el esquema del autor dentro del post
    # dump_only=True asegura que solo se use para serializar (no para cargar)
    author = fields.Nested(EmbeddedUserSchema, dump_only=True)
    
    # Formato de fecha estándar para el JSON
    timestamp = fields.DateTime(format="%Y-%m-%d %H:%M:%S", dump_only=True)
    last_edited = fields.DateTime(format="%Y-%m-%d %H:%M:%S", dump_only=True)


# --- Esquema para Validación y Creación/Actualización (Input) ---
# Usado para validar el JSON que recibimos en los métodos POST y PUT/PATCH
class PostCreateUpdateSchema(ma.Schema):
    """Esquema para validar la entrada de datos (POST/PUT)."""
    
    title = fields.String(
        required=True, 
        validate=validate.Length(min=5, max=255),
        error_messages={"required": "El título es obligatorio."}
    )
    
    body = fields.String(
        required=True, 
        validate=validate.Length(min=10),
        error_messages={"required": "El cuerpo del contenido es obligatorio."}
    )
    
    # El estado solo puede ser uno de estos valores
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            choices=["draft", "published", "archived"], 
            labels=["Borrador", "Publicado", "Archivado"]
        ),
        error_messages={"required": "El estado es obligatorio."}
    )

# Instancias del esquema para usar en las rutas de la API
# Un objeto (para detalle o creación)
post_schema = PostSchema() 
# Una lista de objetos (para la lista principal)
posts_schema = PostSchema(many=True) 

# Instancia del esquema para validar la entrada
post_input_schema = PostCreateUpdateSchema()