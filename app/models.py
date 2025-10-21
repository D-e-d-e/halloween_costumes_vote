from app import db
from datetime import datetime
import uuid

class Costume(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True) # Percorso relativo al file QR code nell'app/static/qr_codes

    votes = db.relationship('Vote', backref='costume', lazy=True)

    def __repr__(self):
        return f"<Costume {self.name}>"

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    costume_id = db.Column(db.String(36), db.ForeignKey('costume.id'), nullable=False)
    voter_identifier = db.Column(db.String(255), nullable=False) # ID univoco per il votante (dal cookie)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Vote for Costume {self.costume_id} by {self.voter_identifier}>"
    
from werkzeug.security import generate_password_hash, check_password_hash # Per hash delle password

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"