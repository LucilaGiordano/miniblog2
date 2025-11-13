from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.forms import LoginForm, RegisterForm, PostForm, ComentarioForm
from app.models import Usuario, Post, Comentario, Categoria
from app import db

bp = Blueprint('main', __name__)

# Context processor para categorías
@bp.app_context_processor
def inject_categorias():
    categorias = Categoria.query.all()
    return dict(categorias=categorias)

# ----------------------------
# RUTAS PRINCIPALES
# ----------------------------
@bp.route('/')
@bp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=5)
    return render_template('index.html', posts=posts)

# ----------------------------
# LOGIN
# ----------------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

# ----------------------------
# REGISTER
# ----------------------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = Usuario(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Usuario registrado con éxito', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

# ----------------------------
# LOGOUT
# ----------------------------
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('main.index'))

# ----------------------------
# CREAR POST
# ----------------------------
@bp.route('/post/nuevo', methods=['GET', 'POST'])
@login_required
def crear_post():
    form = PostForm()
    form.categorias.choices = [(c.id, c.nombre) for c in Categoria.query.all()]
    if form.validate_on_submit():
        categoria = Categoria.query.get(form.categorias.data)
        post = Post(
            titulo=form.titulo.data,
            contenido=form.contenido.data,
            autor=current_user
        )
        if categoria:
            post.categorias.append(categoria)
        db.session.add(post)
        db.session.commit()
        flash('Post creado con éxito', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_post.html', form=form)

# ----------------------------
# VER POST + COMENTARIOS
# ----------------------------
@bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def ver_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = ComentarioForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            comentario = Comentario(
                texto=form.texto.data,
                autor=current_user,
                post=post
            )
            db.session.add(comentario)
            db.session.commit()
            flash('Comentario agregado', 'success')
            return redirect(url_for('main.ver_post', post_id=post.id))
        else:
            flash('Debes iniciar sesión para comentar', 'warning')
            return redirect(url_for('main.login'))
    return render_template('post.html', post=post, form=form)

# ----------------------------
# POSTS POR CATEGORÍA
# ----------------------------
@bp.route('/categoria/<nombre>')
def posts_por_categoria(nombre):
    categoria = Categoria.query.filter_by(nombre=nombre).first_or_404()
    posts = Post.query.join(Post.categorias).filter(Categoria.id == categoria.id).order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)
