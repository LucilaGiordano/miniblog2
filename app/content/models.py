from ...extensions import db
from datetime import datetime

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)
    
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_edited = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clave foránea que apunta a la tabla 'usuarios'
    author_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    def __repr__(self):
        return f'<Post {self.id}: {self.title}>'