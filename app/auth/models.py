from ...extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from enum import Enum 
from sqlalchemy.exc import NoResultFound

# Constantes de Roles (IDs) para la lógica de permisos
class RoleEnum(Enum):
    READER = 1
    EDITOR = 2
    ADMIN = 3

# Modelo de Roles (LECTOR, EDITOR, ADMIN)
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

# Modelo de Usuario (Hereda de UserMixin para Flask-Login)
class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=RoleEnum.READER.value) 

    # IMPORTANTE: Esta relación conecta con el modelo 'Post' que está en app/content/models.py
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # CRUCIAL: Lógica de permisos para la API
    def can(self, required_role_id: int):
        """Verifica si el ID del rol del usuario es igual o mayor al ID requerido."""
        return self.role_id >= required_role_id

    def __repr__(self):
        return f'<User {self.username}>'

# Función de carga de usuario requerida por Flask-Login
from flask_login import current_app as current_app_login
@current_app_login.user_loader
def load_user(user_id):
    from app.extensions import db 
    
    try:
        # Usamos db.session.get() para cargar el usuario por su clave primaria
        return db.session.get(User, int(user_id))
    except (ValueError, NoResultFound):
        return None