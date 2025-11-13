from app import db 
from passlib.hash import sha256_crypt
from datetime import datetime

# --- Tablas de Unión (Many-to-Many) ---
# Define la tabla de unión entre Post y Categoria
post_categoria = db.Table('post_categoria',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('categoria_id', db.Integer, db.ForeignKey('categoria.id'), primary_key=True)
)

# --- Modelos Principales ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user') 
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones: Un Usuario tiene muchos Posts y muchos Comentarios
    posts = db.relationship('Post', backref='autor_post', lazy='dynamic', cascade="all, delete-orphan")
    comentarios = db.relationship('Comentario', backref='autor_comentario', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Usuario {self.username}>'

    def set_password(self, password):
        self.password_hash = sha256_crypt.hash(password)

    def check_password(self, password):
        return sha256_crypt.verify(password, self.password_hash)

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(64), unique=True, nullable=False)

    def __repr__(self):
        return f'<Categoria {self.nombre}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    # Relación: Un Post pertenece a un Usuario (autor)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    # Relación: Un Post tiene muchos Comentarios
    comentarios = db.relationship('Comentario', backref='post_parent', lazy='dynamic', cascade="all, delete-orphan")

    # Relación Muchos a Muchos: Un Post tiene muchas Categorías
    categorias = db.relationship(
        'Categoria', 
        secondary=post_categoria, 
        lazy='dynamic', 
        backref=db.backref('posts', lazy='dynamic'),
        cascade="all, delete" 
    )

    def __repr__(self):
        return f'<Post {self.titulo}>'


class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_visible = db.Column(db.Boolean, default=True) 

    # Relaciones: Un Comentario pertenece a un Usuario (autor) y un Post
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f'<Comentario {self.id}>'