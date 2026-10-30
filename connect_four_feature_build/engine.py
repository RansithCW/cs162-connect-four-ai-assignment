"""Pure Connect Four rules and a small deterministic computer opponent."""

ROWS, COLS = 6, 7
HUMAN, BOT = 1, 2
ORDER = (3, 2, 4, 1, 5, 0, 6)


def empty_board():
    return [[0] * COLS for _ in range(ROWS)]


def legal_moves(board):
    return [col for col in ORDER if board[0][col] == 0]


def drop(board, col, player):
    if not isinstance(col, int) or not 0 <= col < COLS or board[0][col]:
        raise ValueError('Invalid or full column.')
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return row


def winner(board):
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if not p:
                continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if all(0 <= r + i * dr < ROWS and
                       0 <= c + i * dc < COLS and
                       board[r + i * dr][c + i * dc] == p
                       for i in range(4)):
                    return p
    return 0


def outcome(board):
    w = winner(board)
    if w == HUMAN:
        return 'win'
    if w == BOT:
        return 'loss'
    if not legal_moves(board):
        return 'draw'
    return 'playing'


def from_moves(moves):
    board = empty_board()
    for i, col in enumerate(moves):
        drop(board, col, HUMAN if i % 2 == 0 else BOT)
    return board


def hypothetical(board, col, player):
    copy = [row[:] for row in board]
    drop(copy, col, player)
    return copy


def winning_move(board, player):
    for col in legal_moves(board):
        if winner(hypothetical(board, col, player)) == player:
            return col
    return None


def score(board):
    """Heuristic for the bot: reward central control and open lines of four."""
    total = 0
    for r in range(ROWS):
        if board[r][3] == BOT:
            total += 4
        elif board[r][3] == HUMAN:
            total -= 4
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in directions:
                end_r, end_c = r + 3 * dr, c + 3 * dc
                if not (0 <= end_r < ROWS and 0 <= end_c < COLS):
                    continue
                cells = [board[r + i * dr][c + i * dc] for i in range(4)]
                b, h = cells.count(BOT), cells.count(HUMAN)
                if h == 0:
                    total += (0, 1, 5, 30, 10000)[b]
                if b == 0:
                    total -= (0, 1, 6, 35, 10000)[h]
    return total


def bot_move(board):
    """Win > block > avoid immediate reply wins > heuristic and center."""
    options = legal_moves(board)
    if not options:
        return None
    for player in (BOT, HUMAN):
        move = winning_move(board, player)
        if move is not None:
            return move
    best = None
    best_value = float('-inf')
    for col in options:
        next_board = hypothetical(board, col, BOT)
        # Avoid creating a position in which the human wins next turn.
        unsafe = winning_move(next_board, HUMAN) is not None
        value = score(next_board) - (100000 if unsafe else 0)
        # A modest look-ahead: prefer moves leaving the human few good replies.
        responses = legal_moves(next_board)
        if responses and not unsafe:
            value -= max(score(hypothetical(next_board, reply, HUMAN)) * -0.2
                         for reply in responses)
        if value > best_value:
            best, best_value = col, value
    return best
