# Connect Four (Flask + SQLite)

A local, server-rendered game against a depth-3 minimax bot. No JavaScript or online services.

## Windows PowerShell setup

```powershell
cd path\to\connect_four
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app:create_app init-db
python -m flask --app app:create_app run --debug
```

Visit http://127.0.0.1:5000. Stop with Ctrl+C. If activation is blocked, run `Set-ExecutionPolicy -Scope Process Bypass` in that PowerShell window and retry. In subsequent sessions, reactivate `.venv` and run the last command. SQLite data lives in `instance/connect_four.db`. `init-db` creates missing tables without erasing games.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Design

- `app.py`: initializes Flask, extensions, blueprints, and the database CLI command.
- `models.py`: User, Game, and Move tables; `Move.number` fixes turn order.
- `auth.py`: registration, login, logout, password hashing, and session guard.
- `game_logic.py`: standalone rules, reconstruction, and computer tactics.
- `game_routes.py`: private game endpoints, replay, and derived statistics.
- `templates/`: Jinja HTML; `_board.html` is shared between play and replay.
- `static/style.css`: board and page styling.
- `tests/test_game_logic.py`: rules and bot unit tests.

A game stores status and moves, not a second copy of the board. Move columns are zero-based in storage and history; buttons display 1–7. The browser sends one human move, then the server saves both turns in one database transaction. The bot first checks immediate wins and blocks, then uses depth-3 minimax (computer move, human reply, computer move). A simple score rewards potential four-in-a-row groups and center control. It does not use alpha-beta pruning or solve the game perfectly.

## Manual checklist

- [ ] Register user A, logout, log in again; incorrect password fails.
- [ ] Start a game and play several turns; yellow pieces fall to lowest empty cells and red computer moves follow.
- [ ] Check horizontal, vertical, and both diagonal wins in rule tests.
- [ ] Send a full-column move, a noninteger column, and an out-of-range column; none creates a move.
- [ ] After a finished game, attempt another move; status and history stay unchanged.
- [ ] Restart Flask and resume a saved unfinished game; moves remain.
- [ ] Replay from move 0 to the final move using Next and Previous.
- [ ] Verify statistics count only completed games and calculate wins / completed * 100.
- [ ] Register user B; user A's games and statistics do not appear. Directly request A's game and replay URLs while logged in as B; both return 404.

## Local-only security notes

The default secret key is for local development only. For any shared deployment, set a unique `SECRET_KEY`, disable debug mode, and add CSRF protection to forms. Do not expose the development server to the public internet.
