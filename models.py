from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ================== USER ==================
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'student' or 'admin'

    # RELATIONSHIP ✅ (IMPORTANT)
    tickets = db.relationship('Ticket', backref='student', lazy=True)

# ================== TICKET ==================
class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default='Pending')
    priority = db.Column(db.String(10), default='Medium')

    admin_response = db.Column(db.Text)

    file = db.Column(db.String(200))  # filename

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )