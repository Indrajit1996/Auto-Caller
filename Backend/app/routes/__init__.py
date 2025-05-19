from .auth import auth_blueprint

def register_routes(app):
    app.register_blueprint(auth_blueprint)
