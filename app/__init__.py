import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from datetime import timedelta 

# ----------------------------------------------------------------------
# NOTA IMPORTANTE: Esta línea debe coincidir con la ubicación de tu Config
from config import Config
# ----------------------------------------------------------------------

# --- Inicialización de Extensiones ---
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)
jwt = JWTManager(app)

# ----------------------------------------------------
# REGISTRO DE RUTAS DE LA API (MethodView)
# ----------------------------------------------------

# Importamos las vistas API (las importaciones son relativas al paquete 'app')
from .views.auth_views import RegisterAPI, LoginAPI 
from .views.post_views import PostListAPI, PostDetailAPI 
from .views.comment_views import CommentListAPI, CommentDetailAPI 
from .views.category_views import CategoryListAPI, CategoryDetailAPI 

# Rutas de Autenticación
app.add_url_rule(
    '/api/register', 
    view_func=RegisterAPI.as_view('register_api'), 
    methods=['POST']
)
app.add_url_rule(
    '/api/login', 
    view_func=LoginAPI.as_view('login_api'), 
    methods=['POST']
)

# Rutas de Posts
app.add_url_rule(
    '/api/posts', 
    view_func=PostListAPI.as_view('post_list_api'), 
    methods=['GET', 'POST']
)
app.add_url_rule(
    '/api/posts/<int:post_id>', 
    view_func=PostDetailAPI.as_view('post_detail_api'), 
    methods=['GET', 'PUT', 'DELETE']
)

# Rutas de Comentarios
app.add_url_rule(
    # Para crear o ver comentarios de un post específico
    '/api/posts/<int:post_id>/comments', 
    view_func=CommentListAPI.as_view('comment_list_api'), 
    methods=['GET', 'POST']
)
app.add_url_rule(
    # Para editar o eliminar un comentario por su ID
    '/api/comments/<int:comment_id>', 
    view_func=CommentDetailAPI.as_view('comment_detail_api'), 
    methods=['PUT', 'DELETE']
)

# Rutas de Categorías
app.add_url_rule(
    '/api/categories', 
    view_func=CategoryListAPI.as_view('category_list_api'), 
    methods=['GET', 'POST']
)
app.add_url_rule(
    '/api/categories/<int:category_id>', 
    view_func=CategoryDetailAPI.as_view('category_detail_api'), 
    methods=['GET', 'PUT', 'DELETE']
)


# Opcional: Registra las rutas web tradicionales (si tienes un archivo 'app/routes.py')
from . import routes