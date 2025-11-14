import os
from flask import Flask, jsonify
from datetime import timedelta
from flask_login import LoginManager

from app.extensions import db, migrate, jwt, ma 

login = LoginManager()
login.login_view = 'auth.login_api'

# Importamos modelos para que Flask-Migrate los detecte
from app.auth import models as auth_models
from app.content import models as content_models

from . import commands

def create_app(config_class=None):
    app = Flask(__name__)

    if config_class:
        app.config.from_object(config_class)
    else:
        try:
            from config import Config
        except ImportError:
            class Config:
                SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-flask'
                SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///miniblog.db'
                SQLALCHEMY_TRACK_MODIFICATIONS = False
                JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secreto-jwt-api'
                JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

            app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    login.init_app(app)

    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return str(user_id)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from app.auth.models import User
        identity = jwt_data["sub"]
        return db.session.get(User, identity)

    @jwt.invalid_token_loader
    def invalid_token(error):
        return jsonify({"msg": "Token inválido"}), 401

    @jwt.unauthorized_loader
    def unauthorized(error):
        return jsonify({"msg": "Token no provisto"}), 401

    @jwt.expired_token_loader
    def expired(_h, _d):
        return jsonify({"msg": "Token expirado"}), 401

    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.content.routes import bp as content_bp
    app.register_blueprint(content_bp, url_prefix='/api/content')

    from .api_routes import api_bp
    app.register_blueprint(api_bp)

    commands.register_commands(app)

    return app
