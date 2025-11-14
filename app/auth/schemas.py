from app.extensions import ma
from .models import User, Role

# Esquema para el modelo Role
class RoleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Role
        # Campos a exponer
        fields = ('id', 'name')

# Esquema para el modelo User
class UserSchema(ma.SQLAlchemyAutoSchema):
    # Incluir el rol anidado usando el esquema de Role
    role = ma.Nested(RoleSchema) 

    class Meta:
        model = User
        # Campos a exponer. Excluimos 'password_hash' por seguridad.
        fields = ('id', 'username', 'email', 'role', 'role_id') 
        # Cargar la relación 'role' automáticamente
        load_instance = True 
        include_relationships = True 

# Instancias del esquema
role_schema = RoleSchema()
user_schema = UserSchema()
users_schema = UserSchema(many=True)