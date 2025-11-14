from ...extensions import db
from datetime import datetime

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)

    # NEW (para alinearlo a la consigna)
    is_published = db.Column(db.Boolean, default=False, nullable=False)

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_edited = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
