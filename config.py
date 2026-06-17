import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Security key
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-later")

    # DATABASE (Render PostgreSQL compatible)
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Fix for Render PostgreSQL (VERY IMPORTANT)
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///" + os.path.join(basedir, "instance", "safewatch.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------
    # EMAIL SETTINGS
    # -----------------------

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    # Replace with your Gmail address
    MAIL_USERNAME = "chilzchiwenite@gmail.com"

    # Replace with your Gmail App Password
    MAIL_PASSWORD = "mfafbpylaryvvbxi"

    MAIL_DEFAULT_SENDER = "chilzchiwenite@gmail.com"