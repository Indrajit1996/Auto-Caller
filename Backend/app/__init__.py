from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from .config import Config

mail = Mail()
serializer = URLSafeTimedSerializer('2e3a4fa3-98c9-4d9e-b3e7-e2aa3f781234')  # move to env for prod

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

    mail.init_app(app)

    from app.routes import register_routes
    register_routes(app)

    return app
