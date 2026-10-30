import unittest
from game_logic import empty_board, legal_move, drop_piece, has_won, is_draw, board_from_moves, computer_move


class RulesTests(unittest.TestCase):
    def test_horizontal_vertical_and_diagonals(self):
        for coordinates in (
            [(5, 0), (5, 1), (5, 2), (5, 3)],
            [(5, 0), (4, 0), (3, 0), (2, 0)],
            [(5, 0), (4, 1), (3, 2), (2, 3)],
            [(2, 0), (3, 1), (4, 2), (5, 3)],
        ):
            board = empty_board()
            for row, col in coordinates:
                board[row][col] = 1
            self.assertTrue(has_won(board, 1))

    def test_full_column_rejected(self):
        board = empty_board()
        for _ in range(6):
            drop_piece(board, 0, 1)
        self.assertFalse(legal_move(board, 0))
        with self.assertRaises(ValueError):
            drop_piece(board, 0, 1)

    def test_reconstruction(self):
        board = board_from_moves([3, 4, 3])
        self.assertEqual(board[5][3], 1)
        self.assertEqual(board[4][3], 1)
        self.assertEqual(board[5][4], 2)

    def test_bot_wins_and_blocks(self):
        board = empty_board()
        for col in (0, 1, 2):
            drop_piece(board, col, 2)
        self.assertEqual(computer_move(board), 3)
        board = empty_board()
        for col in (0, 1, 2):
            drop_piece(board, col, 1)
        self.assertEqual(computer_move(board), 3)

    def test_draw(self):
        board = empty_board()
        self.assertFalse(is_draw(board))
        # A full position without a horizontal, vertical, or diagonal four.
        cells = [
            [2, 1, 2, 2, 2, 1, 1],
            [2, 2, 2, 1, 1, 1, 2],
            [1, 1, 2, 2, 2, 1, 1],
            [2, 2, 1, 1, 1, 2, 1],
            [2, 2, 1, 2, 1, 2, 2],
            [1, 1, 1, 2, 2, 1, 2],
        ]
        board = cells
        self.assertFalse(has_won(board, 1))
        self.assertFalse(has_won(board, 2))
        self.assertTrue(is_draw(board))


if __name__ == "__main__":
    unittest.main()
