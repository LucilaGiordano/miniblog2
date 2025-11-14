from flask import Blueprint
# 1. Importar las vistas de Autenticación
from .views.auth_views import RegisterAPI, LoginAPI, UserDetailAPI, UserListAPI
# 2. Importar las vistas de Categorías
from .views.category_views import CategoryListAPI, CategoryDetailAPI
# 3. Importar las vistas de Posts
from .views.post_views import PostListAPI, PostDetailAPI
# 4. Importar las vistas de Comentarios
from .views.comment_views import CommentListAPI, CommentDetailAPI


# Definición del Blueprint para las rutas de la API
# Usaremos /api/v1/ como prefijo base para todos los endpoints.
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


# ----------------------------------------------------------------------
# 1. RUTAS DE AUTENTICACIÓN Y USUARIOS
# ----------------------------------------------------------------------

# POST: Registrar nuevo usuario (Rol por defecto: READER) -> /api/v1/auth/register
api_bp.add_url_rule(
    '/auth/register',
    view_func=RegisterAPI.as_view('register_api'),
    methods=['POST']
)

# POST: Iniciar sesión y obtener JWT -> /api/v1/auth/login
api_bp.add_url_rule(
    '/auth/login',
    view_func=LoginAPI.as_view('login_api'),
    methods=['POST']
)

# GET: Obtener detalles del usuario autenticado -> /api/v1/auth/me
api_bp.add_url_rule(
    '/auth/me',
    view_func=UserDetailAPI.as_view('user_detail_api'),
    methods=['GET']
)

# GET: Listar todos los usuarios (Solo ADMIN) -> /api/v1/users
api_bp.add_url_rule(
    '/users',
    view_func=UserListAPI.as_view('user_list_api'),
    methods=['GET']
)


# ----------------------------------------------------------------------
# 2. RUTAS DE CATEGORÍAS
# ----------------------------------------------------------------------

# GET: Listar, POST: Crear (Solo ADMIN/EDITOR) -> /api/v1/categories
api_bp.add_url_rule(
    '/categories',
    view_func=CategoryListAPI.as_view('category_list_api'),
    methods=['GET', 'POST']
)

# GET: Detalle, PUT: Editar, DELETE: Eliminar (Solo ADMIN/EDITOR) -> /api/v1/categories/<int:category_id>
api_bp.add_url_rule(
    '/categories/<int:category_id>',
    view_func=CategoryDetailAPI.as_view('category_detail_api'),
    methods=['GET', 'PUT', 'DELETE']
)


# ----------------------------------------------------------------------
# 3. RUTAS DE POSTS
# ----------------------------------------------------------------------

# GET: Listar, POST: Crear (Solo ADMIN/EDITOR) -> /api/v1/posts
api_bp.add_url_rule(
    '/posts',
    view_func=PostListAPI.as_view('post_list_api'),
    methods=['GET', 'POST']
)

# GET: Detalle, PUT: Editar, DELETE: Eliminar (Control de Roles/Autoría) -> /api/v1/posts/<int:post_id>
api_bp.add_url_rule(
    '/posts/<int:post_id>',
    view_func=PostDetailAPI.as_view('post_detail_api'),
    methods=['GET', 'PUT', 'DELETE']
)


# ----------------------------------------------------------------------
# 4. RUTAS DE COMENTARIOS
# ----------------------------------------------------------------------

# GET: Listar por Post, POST: Crear Comentario (Lector/Autorizado) -> /api/v1/posts/<int:post_id>/comments
api_bp.add_url_rule(
    '/posts/<int:post_id>/comments',
    view_func=CommentListAPI.as_view('comment_list_api'),
    methods=['GET', 'POST']
)

# PUT: Editar, DELETE: Eliminar (Control de Roles/Autoría) -> /api/v1/comments/<int:comment_id>
api_bp.add_url_rule(
    '/comments/<int:comment_id>',
    view_func=CommentDetailAPI.as_view('comment_detail_api'),
    methods=['PUT', 'DELETE']
)