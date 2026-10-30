"""Create games, make moves, show history, replay and statistics."""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from auth import login_required
from game_logic import board_from_moves, computer_move, drop_piece, has_won, is_draw, legal_move
from models import db, Game, Move

games_bp = Blueprint("games", __name__)


def my_game(game_id):
    game = db.session.get(Game, game_id)
    if game is None or game.user_id != session["user_id"]:
        abort(404)
    return game


def columns(game):
    return [move.column for move in game.moves]


def add_move(game, col, player):
    db.session.add(Move(game_id=game.id, number=len(game.moves), column=col, player=player))
    # Keep relationship's in-memory list in sync for correct numbering.
    db.session.flush()
    db.session.expire(game, ["moves"])


@games_bp.route("/games")
@login_required
def dashboard():
    games = db.session.execute(
        db.select(Game).where(Game.user_id == session["user_id"]).order_by(Game.id.desc())
    ).scalars().all()
    return render_template("dashboard.html", games=games)


@games_bp.route("/games/new", methods=["POST"])
@login_required
def new_game():
    game = Game(user_id=session["user_id"])
    db.session.add(game)
    db.session.commit()
    return redirect(url_for("games.play", game_id=game.id))


@games_bp.route("/games/<int:game_id>")
@login_required
def play(game_id):
    game = my_game(game_id)
    board = board_from_moves(columns(game))
    return render_template("play.html", game=game, board=board)


@games_bp.route("/games/<int:game_id>/move", methods=["POST"])
@login_required
def move(game_id):
    game = my_game(game_id)
    if game.status != "playing":
        flash("This game is already finished.")
        return redirect(url_for("games.play", game_id=game.id))

    raw_column = request.form.get("column", "")
    try:
        col = int(raw_column)
    except ValueError:
        abort(400, "Column must be an integer")
    if str(col) != raw_column:
        abort(400, "Invalid column")

    board = board_from_moves(columns(game))
    if not legal_move(board, col):
        flash("That column is not available.")
        return redirect(url_for("games.play", game_id=game.id))

    drop_piece(board, col, 1)
    add_move(game, col, 1)
    if has_won(board, 1):
        game.status = "won"
    elif is_draw(board):
        game.status = "draw"
    else:
        bot_col = computer_move(board)
        drop_piece(board, bot_col, 2)
        add_move(game, bot_col, 2)
        if has_won(board, 2):
            game.status = "lost"
        elif is_draw(board):
            game.status = "draw"
    db.session.commit()
    return redirect(url_for("games.play", game_id=game.id))


@games_bp.route("/games/<int:game_id>/replay")
@login_required
def replay(game_id):
    game = my_game(game_id)
    history = columns(game)
    try:
        step = int(request.args.get("step", "0"))
    except ValueError:
        abort(400)
    if not 0 <= step <= len(history):
        abort(400)
    board = board_from_moves(history[:step])
    return render_template("replay.html", game=game, board=board,
                           step=step, total=len(history))


@games_bp.route("/statistics")
@login_required
def statistics():
    games = db.session.execute(db.select(Game).where(Game.user_id == session["user_id"])).scalars().all()
    counts = {status: sum(g.status == status for g in games) for status in ("won", "lost", "draw")}
    total = sum(counts.values())
    percentage = 100 * counts["won"] / total if total else 0
    return render_template("statistics.html", counts=counts, total=total, percentage=percentage)
