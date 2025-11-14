from datetime import datetime
from . import db, ma
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import fields
import enum

# --- Modelos de Base de Datos ---

# Enum para definir los roles (NOMENCLATURA UNIFICADA)
class RoleName(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    READER = "reader"

# Tabla de Roles
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum(RoleName), unique=True, nullable=False)

    usuarios = db.relationship('Usuario', backref='role', lazy=True)

    def __repr__(self):
        return f"Role('{self.name.value}')"

# Tabla de Usuarios
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))

    # FK al rol
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    # NEW
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='commenter', lazy='dynamic')

    def __repr__(self):
        return f'<Usuario {self.username}>'

    # Utilidades para password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Tabla de Categorías
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

    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")

# Tabla de Comentarios
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    is_visible = db.Column(db.Boolean, default=True, nullable=False)

# --- Esquemas de Marshmallow ---

class RoleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Role
        load_instance = True
        include_relationships = True
        fields = ('id', 'name')

class UsuarioSchema(ma.SQLAlchemyAutoSchema):
    role = fields.Nested(RoleSchema, only=("name",), required=True)

    class Meta:
        model = Usuario
        load_instance = True
        include_relationships = True
        fields = ('id', 'username', 'email', 'role')

class PostSchema(ma.SQLAlchemyAutoSchema):
    author = fields.Nested(UsuarioSchema, only=("id", "username", "email", "role"))
    category = fields.Nested('CategorySchema', only=("id", "name"))

    user_id = fields.Int(required=False, load_only=True)
    category_id = fields.Int(required=True, load_only=True)

    class Meta:
        model = Post
        load_instance = True
        include_fk = True
        fields = ('id', 'title', 'body', 'timestamp', 'author', 'category')

class CommentSchema(ma.SQLAlchemyAutoSchema):
    commenter = fields.Nested(UsuarioSchema, only=("id", "username", "role"))

    class Meta:
        model = Comment
        load_instance = True
        include_fk = True
        fields = ('id', 'body', 'timestamp', 'user_id', 'post_id', 'commenter')

class CategorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        load_instance = True
        include_relationships = True
        fields = ('id', 'name', 'description')

# Instancias
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
