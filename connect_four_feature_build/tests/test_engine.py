import unittest
from engine import (BOT, HUMAN, bot_move, drop, empty_board,
                    from_moves, legal_moves, outcome, winner)


class EngineTests(unittest.TestCase):
    def test_horizontal(self):
        b = empty_board()
        for c in range(4):
            drop(b, c, HUMAN)
        self.assertEqual(winner(b), HUMAN)

    def test_vertical(self):
        b = empty_board()
        for _ in range(4):
            drop(b, 3, BOT)
        self.assertEqual(winner(b), BOT)

    def test_diagonals(self):
        for reverse in (False, True):
            b = empty_board()
            for c in range(4):
                col = 6 - c if reverse else c
                for _ in range(c):
                    drop(b, col, BOT)
                drop(b, col, HUMAN)
            self.assertEqual(winner(b), HUMAN)

    def test_full_column(self):
        b = empty_board()
        for i in range(6):
            drop(b, 0, HUMAN if i % 2 else BOT)
        self.assertNotIn(0, legal_moves(b))
        with self.assertRaises(ValueError):
            drop(b, 0, HUMAN)
        with self.assertRaises(ValueError):
            drop(b, -1, HUMAN)

    def test_bot_wins(self):
        b = empty_board()
        for c in range(3):
            drop(b, c, BOT)
        self.assertEqual(bot_move(b), 3)

    def test_bot_blocks(self):
        b = empty_board()
        for c in range(3):
            drop(b, c, HUMAN)
        self.assertEqual(bot_move(b), 3)

    def test_bot_prefers_own_win_over_block(self):
        b = empty_board()
        for c in range(3):
            drop(b, c, HUMAN)
            drop(b, c, BOT)
        self.assertEqual(bot_move(b), 3)

    def test_center_opening(self):
        self.assertEqual(bot_move(empty_board()), 3)

    def test_rebuild(self):
        b = from_moves([3, 2, 3, 4])
        self.assertEqual(b[5][3], HUMAN)
        self.assertEqual(b[4][3], HUMAN)
        self.assertEqual(b[5][2], BOT)
        self.assertEqual(b[5][4], BOT)

    def test_draw(self):
        # A full board without four connected pieces (searched once, fixed fixture).
        b = [[1,1,2,2,1,1,2],
             [2,2,1,1,2,2,1],
             [1,1,2,2,1,1,2],
             [2,2,1,1,2,2,1],
             [1,1,2,2,1,1,2],
             [2,2,1,1,2,2,1]]
        self.assertEqual(outcome(b), 'draw')


if __name__ == '__main__':
    unittest.main()
