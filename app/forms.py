from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    email = StringField('Correo', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar sesión')

class RegisterForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Correo', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    submit = SubmitField('Registrarse')

class PostForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired(), Length(max=120)])
    contenido = TextAreaField('Contenido', validators=[DataRequired()])
    categorias = SelectField('Categoría', coerce=int)  # importante el coerce=int
    submit = SubmitField('Publicar')

class ComentarioForm(FlaskForm):
    texto = TextAreaField('Comentario', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Enviar')
