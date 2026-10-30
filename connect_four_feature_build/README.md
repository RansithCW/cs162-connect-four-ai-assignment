# Connect Four — local Flask web app

A two-player *turn-based* Connect Four game where the second player is a rule-based computer. The human always moves first (red). No online services are needed while running the app.

## Requirements

- Windows 10/11 and Python 3.10 or later
- Flask 3.x (installed once with pip; internet may be needed **for installation only**)
- No external database, APIs, machine learning, JavaScript frameworks, or API keys

## Start on Windows PowerShell

Open PowerShell in the extracted `connect_four` folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If activation is blocked by PowerShell policy, **skip activation** and use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5000** in your browser. Press `Ctrl+C` in PowerShell to stop. To restart next time, run `python app.py` after activating the same virtual environment (or use the explicit `.venv` Python path). The database and secret key are created automatically in `instance/` and survive restart. Do not delete `instance/` if you want to keep your data. You can use the app fully offline after Flask has been installed.

## Tests

From the project folder with Flask installed:

```powershell
python -m unittest discover -s tests -v
```

## Files

- `app.py` — Flask app, registration/login/logout, SQLite tables, per-user access checks, game saving, and replay routes.
- `engine.py` — board rules, win/draw detection, history reconstruction, and rule-based computer opponent.
- `templates/base.html` — shared page layout and navigation.
- `templates/auth.html` — register/login forms.
- `templates/dashboard.html` — games list and statistics.
- `templates/game.html` — board, playable columns, move list, and replay controls.
- `static/style.css` — responsive visual styling.
- `tests/` — pure rules tests and Flask/SQLite integration tests.
- `requirements.txt` — one Python dependency, Flask.
- `instance/` — auto-generated local SQLite database and persistent session signing key (ignored by Git).

## Design choices

Games store their ordered moves in a JSON array inside SQLite. Human moves are at even indices; computer moves at odd indices. On every request the server reconstructs the board from saved moves. There is no separate mutable board to become inconsistent with the move history. Outcomes and stats are calculated server-side; stats count completed games only. All game reads and writes filter by both game ID **and authenticated user ID**, so guessing another user's game number does not grant access.

The computer first finds an immediate win, otherwise blocks an immediate human win, and otherwise chooses a legal move using a center/open-lines heuristic. It avoids immediate losing replies where possible. **It is not a mathematically perfect Connect Four solver**; full optimal solving requires a much larger search implementation. The computer responds immediately after each human move, so no additional bot-turn endpoint is needed.

## Manual testing checklist

- [ ] Register `alice`, log in, log out, and log back in. Wrong password is rejected.
- [ ] Registering an existing username produces a clear error. Passwords are not stored as plaintext.
- [ ] Create a game. Red moves first; selecting a column drops a red piece to the lowest free row, followed by a yellow piece.
- [ ] Make multiple moves in one column: pieces stack from bottom up; a full column becomes disabled. Invalid columns cannot alter saved data.
- [ ] Verify horizontal, vertical, `/` and `\\` diagonal wins with planned move sequences; the game stops accepting moves once finished.
- [ ] Verify the computer takes immediate wins and blocks immediate threats; start a fresh game to test each case.
- [ ] Check a full board with no four-in-a-row is a draw (also covered by the automated fixture).
- [ ] Midgame, return to My games, press Resume, and confirm exactly the same board and move history.
- [ ] Stop the server, restart it, log in again, and resume the same game.
- [ ] Finish a game. Confirm it is shown as Won/Lost/Draw and that completed games, wins, losses, draws, and win rate are correct.
- [ ] Open Replay, go to Start, step Next/Previous through each red/yellow move, and jump to End. Ensure board positions match move history.
- [ ] Register `bob`. Confirm Bob's dashboard has no Alice games or statistics, and Bob cannot view, replay, or move Alice's game even by directly typing its URL.
- [ ] Confirm that logout blocks access to game pages; browser back/reload does not bypass the login check.
- [ ] Turn off internet access after installing Flask and repeat registration, gameplay, reload, and replay.

## Scope limitations

This is a local course project, not a deployed multi-user internet service. It does not offer password reset, email verification, rate limiting, admin controls, animation, or a perfect-play solver. Keep the `instance/` directory private; do not commit the SQLite database or secret key. For local development, the app binds to `127.0.0.1` by default.
