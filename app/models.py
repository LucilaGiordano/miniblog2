from datetime import datetime
from . import db, ma
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import fields
import enum

# --- Modelos de Base de Datos ---

# Enum para definir los roles
class RoleName(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    READER = "reader"

# Tabla de Roles (nueva)
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    # El tipo String(20) es suficiente para almacenar el nombre del rol (admin, editor, reader)
    name = db.Column(db.Enum(RoleName), unique=True, nullable=False) 
    
    # Relación uno-a-muchos con la tabla Usuario (un rol tiene muchos usuarios)
    usuarios = db.relationship('Usuario', backref='role', lazy=True) 

    def __repr__(self):
        return f"Role('{self.name.value}')"

# Tabla de Usuarios (CORREGIDA: Usamos 'Usuario' para mantener tu convención)
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    
    # Clave Foránea para el rol
    # Se eliminó el default, la asignación se hará en el código de registro
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    # Relaciones: Un usuario puede tener varios posts y varios comentarios.
    # El backref debe apuntar al nombre de la clase, que es 'Usuario'
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='commenter', lazy='dynamic')

    def __repr__(self):
        return f'<Usuario {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Tabla de Categorías (sin cambios)
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(256), nullable=True)
    posts = db.relationship('Post', backref='category', lazy='dynamic')

# Tabla de Posts
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    # Claves Foráneas
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id')) # Referencia a la tabla 'usuarios'
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    # Relación con comentarios
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")

# Tabla de Comentarios
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    # Claves Foráneas
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id')) # Referencia a la tabla 'usuarios'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

# --- Esquemas de Marshmallow ---

class RoleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Role
        load_instance = True
        include_relationships = True
        fields = ('id', 'name') # Solo exponemos el nombre del rol

# Esquema para Usuario (CORREGIDO: Usamos 'Usuario' y añadimos el campo de rol)
class UsuarioSchema(ma.SQLAlchemyAutoSchema):
    # Usamos Nested para incluir la información del Rol
    role = fields.Nested(RoleSchema, only=("name",), required=True) 

    class Meta:
        model = Usuario
        load_instance = True
        include_relationships = True
        # Excluimos el password_hash por seguridad
        fields = ('id', 'username', 'email', 'role') 

# Esquema para Post
class PostSchema(ma.SQLAlchemyAutoSchema):
    # Anidamos el esquema de Usuario para exponer el autor
    author = fields.Nested(UsuarioSchema, only=("id", "username", "email", "role")) 
    # Anidamos el esquema de Categoría
    category = fields.Nested('CategorySchema', only=("id", "name"))
    
    # Hacemos que los IDs de las claves foráneas sean cargables/editables
    user_id = fields.Int(required=False, load_only=True)
    category_id = fields.Int(required=True, load_only=True)

    class Meta:
        model = Post
        load_instance = True
        include_fk = True # Incluir claves foráneas en la carga (load)
        # Campos que se serializarán (dump)
        fields = ('id', 'title', 'body', 'timestamp', 'author', 'category') 

# Esquema para Comentario
class CommentSchema(ma.SQLAlchemyAutoSchema):
    # Anidamos el esquema de Usuario para exponer el autor del comentario
    commenter = fields.Nested(UsuarioSchema, only=("id", "username", "role"))
    
    # Campos que se serializarán (dump)
    class Meta:
        model = Comment
        load_instance = True
        include_fk = True
        fields = ('id', 'body', 'timestamp', 'user_id', 'post_id', 'commenter')

# Esquema para Categoría
class CategorySchema(ma.SQLAlchemyAutoSchema):
    # Campos que se serializarán (dump)
    class Meta:
        model = Category
        load_instance = True
        include_relationships = True
        fields = ('id', 'name', 'description')

# Inicialización de instancias de esquemas
usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)

role_schema = RoleSchema()
roles_schema = RoleSchema(many=True)

post_schema = PostSchema()
posts_schema = PostSchema(many=True)

comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)