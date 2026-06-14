from db import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    _tablename_ = "user"   # ✅ FIXED (you wrote tablename before)

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="user",
        nullable=False
    )

    reports = db.relationship(
        "Report",
        backref="author",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    state = db.Column(db.String(100), nullable=True)   # 👈 ADD THIS ONLY

    image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)