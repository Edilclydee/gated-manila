from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.extensions import csrf, limiter
    csrf.init_app(app)
    limiter.init_app(app)

    from app import models  # noqa: F401  (registers tables with SQLAlchemy)
    from app.cli import (
        clear_sample_command, create_admin_command, init_db_command, seed_sample_command,
    )
    for command in (init_db_command, create_admin_command, seed_sample_command, clear_sample_command):
        app.cli.add_command(command)

    from app.routes_public import bp as public_bp
    from app.routes_submit import bp as submit_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(submit_bp)

    @app.errorhandler(429)
    def too_many_requests(_err):
        return render_template("message.html", title="Slow down",
                               message="Too many submissions from your connection. Please try again later."), 429

    @app.errorhandler(404)
    def not_found(_err):
        return render_template("message.html", title="Not found",
                               message="We couldn't find that page."), 404

    return app
