from app import db
from passlib.hash import sha256_crypt
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # Almacena el hash
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones (muchos a uno con Post y Comment)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='commenter', lazy='dynamic')

    def __init__(self, username, email, role='user'):
        self.username = username
        self.email = email
        self.role = role

    # Método para hashear la contraseña
    def set_password(self, password):
        self.password_hash = sha256_crypt.hash(password)

    # Método para verificar la contraseña
    def check_password(self, password):
        return sha256_crypt.verify(password, self.password_hash)

    def __repr__(self):
        return f'<Usuario {self.username}>'

class Categoria(db.Model):
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)

    # Relaciones
    posts = db.relationship('Post', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Categoria {self.nombre}>'

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Claves foráneas
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True) # Puede ser nulo

    # Relaciones
    comments = db.relationship('Comment', backref='parent_post', lazy='dynamic')

    def __repr__(self):
        return f'<Post {self.titulo}>'

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Claves foráneas
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.id}>'