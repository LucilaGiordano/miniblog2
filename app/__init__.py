import os
from flask import Flask, jsonify
from datetime import timedelta
from flask_login import LoginManager # 1. Importar Flask-Login

# Importamos las extensiones
from .extensions import db, migrate, jwt, ma 

# 2. Inicializar LoginManager
login = LoginManager()
login.login_view = 'auth.login_api' # Ruta a donde redirigir si no está autenticado

# IMPORTAMOS LOS MODELOS PARA QUE SQLAlchemy Y Flask-Migrate LOS CONOZCAN
# Es crucial que todos los modelos estén importados aquí o en algún lugar
# que se ejecute antes de la inicialización de Flask-Migrate.
from app.auth import models as auth_models
from app.content import models as content_models # <--- NUEVA IMPORTACIÓN

# Importamos los comandos CLI para el registro
from . import commands

def create_app(config_class=None):
    app = Flask(__name__)

    # Configuración
    if config_class:
        app.config.from_object(config_class)
    else:
        try:
            # Intentamos importar la configuración desde un nivel superior
            from ..config import Config 
        except ImportError:
            # Clase de configuración por defecto si no se encuentra el archivo 'config.py'
            class Config:
                SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-flask'
                # Usar la variable de entorno para la URI de la base de datos
                SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///miniblog.db' 
                SQLALCHEMY_TRACK_MODIFICATIONS = False
                JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secreto-jwt-api'
                JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
            
            app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app) 
    
    # 3. Inicializar LoginManager con la aplicación
    login.init_app(app) 

    # --- CONFIGURACIÓN DE JWT PARA EL LOOKUP DE USUARIOS ---

    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        # Cuando se crea un token, se usa el ID del usuario como "sub"
        return str(user_id) 

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        # IMPORTANTE: Usamos el nuevo modelo User
        from app.auth.models import User 
        identity = jwt_data["sub"]
        
        # Buscamos el usuario por su ID
        # db.session.get() es la forma recomendada en SQLAlchemy 2.0
        return db.session.get(User, identity)

    # --- Manejo de Errores JWT (Para respuestas amigables en la API) ---
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"msg": "Token inválido. Acceso denegado."}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({"msg": "Token no provisto o no autorizado."}), 401

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_data):
        return jsonify({"msg": "El token ha expirado."}), 401
    
    # -------------------------------------------------------------------

    # 4. Importar y registrar los Blueprints
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth') 
    
    # IMPORTAR Y REGISTRAR EL BLUEPRINT DE GESTIÓN DE CONTENIDO (Content Manager)
    from app.content.routes import bp as content_bp # <--- NUEVO
    app.register_blueprint(content_bp, url_prefix='/api/content') # <--- NUEVO: Prefijo claro para las rutas de contenido

    # Registro de Vistas (Blueprints)
    from .api_routes import api_bp
    app.register_blueprint(api_bp)

    # Registro de Comandos Personalizados de Flask CLI
    commands.register_commands(app)
    
    return app

# La definición de db, migrate, jwt y ma se movió a app/extensions.py

# Las importaciones de modelos se movieron dentro de create_app para evitar problemas
# de importación circular, pero las mantendremos al final como estaba originalmente
# ya que Flask-Migrate necesita que se carguen de alguna forma.
# Comentamos las originales y dejamos las nuevas dentro de la función y al inicio:

# from app.auth import models