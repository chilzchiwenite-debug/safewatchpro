import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = "secret"

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        basedir,
        "instance",
        "safewatch.db"
    )

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