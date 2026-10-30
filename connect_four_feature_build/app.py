"""Connect Four: Flask routes, SQLite persistence, and account isolation."""
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from engine import BOT, HUMAN, bot_move, drop, empty_board, from_moves, outcome


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=None,
        DATABASE=os.path.join(app.instance_path, 'connect_four.sqlite'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
    if not app.config['SECRET_KEY']:
        key_path = os.path.join(app.instance_path, 'secret_key')
        if not os.path.exists(key_path):
            with open(key_path, 'x', encoding='utf-8') as f:
                f.write(secrets.token_hex(32))
        with open(key_path, encoding='utf-8') as f:
            app.config['SECRET_KEY'] = f.read().strip()

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        conn = g.pop('db', None)
        if conn:
            conn.close()

    with app.app_context():
        conn = db()
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                moves TEXT NOT NULL DEFAULT '[]',
                result TEXT NOT NULL DEFAULT 'playing',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        ''')
        conn.commit()

    def current_user():
        if 'user_id' not in session:
            return None
        return db().execute('SELECT * FROM users WHERE id=?',
                            (session['user_id'],)).fetchone()

    @app.before_request
    def load_user():
        g.user = current_user()
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(24)
        if request.method == 'POST':
            if not secrets.compare_digest(request.form.get('csrf', ''), session['csrf']):
                abort(400, 'Invalid form token. Refresh the page and try again.')

    @app.context_processor
    def helpers():
        return {'csrf': session.get('csrf', '')}

    def login_required(view):
        @wraps(view)
        def inner(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login'))
            return view(*args, **kwargs)
        return inner

    def owned_game(game_id):
        game = db().execute('SELECT * FROM games WHERE id=? AND user_id=?',
                            (game_id, g.user['id'])).fetchone()
        if game is None:
            abort(404)
        return game

    @app.route('/')
    def index():
        return redirect(url_for('dashboard') if g.user else url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            if not 3 <= len(username) <= 30 or not username.isalnum():
                flash('Username must be 3–30 letters or numbers.')
            elif len(password) < 8:
                flash('Password must be at least 8 characters.')
            else:
                try:
                    with db():
                        db().execute('INSERT INTO users(username,password_hash) VALUES (?,?)',
                                     (username, generate_password_hash(password)))
                    flash('Account created. Log in to start playing.')
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    flash('That username already exists.')
        return render_template('auth.html', title='Register', register=True)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = db().execute('SELECT * FROM users WHERE username=?',
                                (request.form.get('username', '').strip(),)).fetchone()
            if user and check_password_hash(user['password_hash'], request.form.get('password', '')):
                session.clear()
                session['user_id'] = user['id']
                session['csrf'] = secrets.token_hex(24)
                return redirect(url_for('dashboard'))
            flash('Incorrect username or password.')
        return render_template('auth.html', title='Log in', register=False)

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        games = db().execute('''SELECT * FROM games WHERE user_id=?
                                ORDER BY updated_at DESC, id DESC''',
                             (g.user['id'],)).fetchall()
        finished = [game for game in games if game['result'] != 'playing']
        wins = sum(game['result'] == 'win' for game in finished)
        losses = sum(game['result'] == 'loss' for game in finished)
        draws = sum(game['result'] == 'draw' for game in finished)
        stats = dict(total=len(finished), wins=wins, losses=losses,
                     draws=draws, rate=100 * wins / len(finished) if finished else 0)
        return render_template('dashboard.html', games=games, stats=stats)

    @app.post('/games')
    @login_required
    def new_game():
        now = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with db():
            cursor = db().execute('''INSERT INTO games(user_id,created_at,updated_at)
                                     VALUES (?,?,?)''', (g.user['id'], now, now))
        return redirect(url_for('game_page', game_id=cursor.lastrowid))

    @app.get('/games/<int:game_id>')
    @login_required
    def game_page(game_id):
        game = owned_game(game_id)
        moves = json.loads(game['moves'])
        board = from_moves(moves)
        # Animate only newly placed pieces, once per successful turn.
        animation = session.pop('animation', None)
        animated = {}
        if animation and animation['game_id'] == game_id:
            previous = from_moves(moves[:animation['start']])
            for i, col in enumerate(moves[animation['start']:]):
                player = HUMAN if (animation['start'] + i) % 2 == 0 else BOT
                row = drop(previous, col, player)
                animated[(row, col)] = 'drop-first' if i == 0 else 'drop-second'
        return render_template('game.html', game=game, board=board,
                               moves=moves, is_replay=False, step=len(moves),
                               animated=animated)

    @app.post('/games/<int:game_id>/move')
    @login_required
    def make_move(game_id):
        # One transaction protects against two tabs updating the same game.
        conn = db()
        conn.execute('BEGIN IMMEDIATE')
        try:
            game = owned_game(game_id)
            if game['result'] != 'playing':
                flash('This game is already finished.')
            else:
                moves = json.loads(game['moves'])
                board = from_moves(moves)
                try:
                    col = int(request.form.get('column', ''))
                    drop(board, col, HUMAN)
                except (ValueError, TypeError):
                    flash('Invalid move: choose a non-full column.')
                else:
                    animation_start = len(moves)
                    moves.append(col)
                    result = outcome(board)
                    if result == 'playing':
                        computer_col = bot_move(board)
                        if computer_col is not None:
                            drop(board, computer_col, BOT)
                            moves.append(computer_col)
                        result = outcome(board)
                    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
                    conn.execute('''UPDATE games SET moves=?, result=?, updated_at=?
                                    WHERE id=? AND user_id=?''',
                                 (json.dumps(moves), result, now, game_id, g.user['id']))
                    session['animation'] = {'game_id': game_id, 'start': animation_start}
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return redirect(url_for('game_page', game_id=game_id))

    @app.get('/games/<int:game_id>/replay')
    @login_required
    def replay(game_id):
        game = owned_game(game_id)
        moves = json.loads(game['moves'])
        try:
            step = int(request.args.get('step', 0))
        except ValueError:
            abort(400)
        if not 0 <= step <= len(moves):
            abort(400)
        return render_template('game.html', game=game, board=from_moves(moves[:step]),
                               moves=moves, is_replay=True, step=step)

    return app


if __name__ == '__main__':
    create_app().run(debug=False)
