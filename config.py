import os

basedir = os.path.abspath(os.path.dirname(_file_))

class Config:
    # -----------------------
    # SECURITY
    # -----------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-later")

    # -----------------------
    # DATABASE (Render PostgreSQL safe)
    # -----------------------
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        "sqlite:///" + os.path.join(basedir, "instance", "safewatch.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------
    # EMAIL SETTINGS (SECURE VERSION)
    # -----------------------
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = MAIL_USERNAME