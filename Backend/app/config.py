import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'sachinrao1947@gmail.com'
    MAIL_PASSWORD = 'kqzyaemoachcfoex'
    MAIL_DEFAULT_SENDER = 'sachinrao1947@gmail.com'
