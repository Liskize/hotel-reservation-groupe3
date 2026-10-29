from flask import Flask

from app import db
from app.config import Config
from app.errors import register_error_handlers


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)
    register_error_handlers(app)

    from app.routes import clients, health, hotels, reservations
    app.register_blueprint(health.bp)
    app.register_blueprint(hotels.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(reservations.bp)
    return app