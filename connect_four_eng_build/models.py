"""Database tables for accounts, games and ordered moves."""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    games = db.relationship("Game", backref="owner", lazy=True)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # playing, won, lost, draw
    status = db.Column(db.String(10), nullable=False, default="playing")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    moves = db.relationship("Move", backref="game", lazy=True,
                            order_by="Move.number", cascade="all, delete-orphan")


class Move(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    column = db.Column(db.Integer, nullable=False)
    player = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint("game_id", "number"),)
