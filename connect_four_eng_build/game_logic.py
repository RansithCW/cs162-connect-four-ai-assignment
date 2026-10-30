"""Connect Four rules. No Flask or database dependencies."""

ROWS = 6
COLS = 7


def empty_board():
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]


def legal_move(board, column):
    return isinstance(column, int) and not isinstance(column, bool) and 0 <= column < COLS and board[0][column] == 0


def drop_piece(board, column, player):
    if player not in (1, 2) or not legal_move(board, column):
        raise ValueError("Invalid move")
    for row in range(ROWS - 1, -1, -1):
        if board[row][column] == 0:
            board[row][column] = player
            return row


def has_won(board, player):
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for row in range(ROWS):
        for col in range(COLS):
            if board[row][col] != player:
                continue
            for dr, dc in directions:
                if all(0 <= row + i * dr < ROWS and
                       0 <= col + i * dc < COLS and
                       board[row + i * dr][col + i * dc] == player
                       for i in range(4)):
                    return True
    return False


def is_draw(board):
    return all(board[0][col] != 0 for col in range(COLS)) and not has_won(board, 1) and not has_won(board, 2)


def board_from_moves(moves):
    board = empty_board()
    for index, column in enumerate(moves):
        drop_piece(board, column, 1 if index % 2 == 0 else 2)
    return board


def score_board(board):
    """Score groups of four; positive scores favor the computer (2)."""
    score = sum(row[3] == 2 for row in board) * 3
    score -= sum(row[3] == 1 for row in board) * 3
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for row in range(ROWS):
        for col in range(COLS):
            for dr, dc in directions:
                end_row, end_col = row + 3 * dr, col + 3 * dc
                if not (0 <= end_row < ROWS and 0 <= end_col < COLS):
                    continue
                cells = [board[row + i * dr][col + i * dc] for i in range(4)]
                bot, human = cells.count(2), cells.count(1)
                if human == 0:
                    score += {0: 0, 1: 1, 2: 5, 3: 50, 4: 1000}[bot]
                if bot == 0:
                    score -= {0: 0, 1: 1, 2: 5, 3: 50, 4: 1000}[human]
    return score


def minimax(board, depth, player):
    """Return the best future score, assuming both sides choose well."""
    if has_won(board, 2):
        return 100000 + depth
    if has_won(board, 1):
        return -100000 - depth
    if depth == 0 or is_draw(board):
        return score_board(board)

    choices = [c for c in (3, 2, 4, 1, 5, 0, 6) if legal_move(board, c)]
    scores = []
    for col in choices:
        trial = [row[:] for row in board]
        drop_piece(trial, col, player)
        scores.append(minimax(trial, depth - 1, 1 if player == 2 else 2))
    return max(scores) if player == 2 else min(scores)


def computer_move(board):
    """Depth-3 minimax: computer, human, computer; center breaks ties."""
    choices = [c for c in (3, 2, 4, 1, 5, 0, 6) if legal_move(board, c)]
    if not choices:
        return None

    # Keep immediate wins and blocks explicit: these are easy to verify.
    for player in (2, 1):
        for col in choices:
            trial = [row[:] for row in board]
            drop_piece(trial, col, player)
            if has_won(trial, player):
                return col

    best_col, best_score = choices[0], float("-inf")
    for col in choices:
        trial = [row[:] for row in board]
        drop_piece(trial, col, 2)
        score = minimax(trial, 2, 1)
        if score > best_score:
            best_col, best_score = col, score
    return best_col
