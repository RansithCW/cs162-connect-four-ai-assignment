"""Flask setup and SQLite initialization."""
import os
from flask import Flask, redirect, session, url_for
from models import db
from auth import auth_bp
from game_routes import games_bp


def create_app(test_config=None):
    app = Flask(__name__)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key-change-me"),
        SQLALCHEMY_DATABASE_URI="sqlite:///connect_four.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(games_bp)

    @app.route("/")
    def index():
        return redirect(url_for("games.dashboard" if "user_id" in session else "auth.login"))

    @app.cli.command("init-db")
    def init_db():
        """Create tables (safe to rerun without deleting data)."""
        db.create_all()
        print("Database tables ready.")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
