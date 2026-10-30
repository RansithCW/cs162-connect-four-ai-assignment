"""Integration tests (need Flask installed: pip install -r requirements.txt)."""
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

from app import create_app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'test.sqlite')
        self.app = create_app({'TESTING': True, 'DATABASE': self.path,
                               'SECRET_KEY': 'test-only-key'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def csrf(self):
        with self.client.session_transaction() as s:
            return s['csrf']

    def register(self, name):
        self.client.get('/register')
        return self.client.post('/register', data={
            'username': name, 'password': 'password123', 'csrf': self.csrf()})

    def login(self, name):
        self.client.get('/login')
        return self.client.post('/login', data={
            'username': name, 'password': 'password123', 'csrf': self.csrf()})

    def logout(self):
        return self.client.post('/logout', data={'csrf': self.csrf()})

    def new_game(self):
        response = self.client.post('/games', data={'csrf': self.csrf()})
        self.assertEqual(response.status_code, 302)
        return int(response.location.rsplit('/', 1)[-1])

    def move(self, game_id, col):
        return self.client.post(f'/games/{game_id}/move',
                                data={'csrf': self.csrf(), 'column': col})

    def record(self, game_id):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute(
                'SELECT moves,result FROM games WHERE id=?',
                (game_id,)
            ).fetchone()

    def test_register_login_and_logout(self):
        self.register('alice')
        self.login('alice')
        self.assertEqual(self.client.get('/dashboard').status_code, 200)
        self.logout()
        self.assertEqual(self.client.get('/dashboard').status_code, 302)

    def test_moves_save_and_replay(self):
        self.register('alice')
        self.login('alice')
        game_id = self.new_game()
        self.assertEqual(self.move(game_id, 3).status_code, 302)
        moves, state = self.record(game_id)
        self.assertEqual(len(json.loads(moves)), 2)
        self.assertEqual(state, 'playing')
        self.assertIn(b'Move 1 of 2',
                      self.client.get(f'/games/{game_id}/replay?step=1').data)
        self.assertEqual(self.client.get(f'/games/{game_id}/replay?step=3').status_code, 400)
        # A fresh Flask app instance pointing to the same db still has the game.
        second = create_app({'TESTING': True, 'DATABASE': self.path, 'SECRET_KEY': 'test-only-key'})
        with second.test_client() as other:
            with other.session_transaction() as s:
                s['user_id'] = 1
            self.assertEqual(other.get(f'/games/{game_id}').status_code, 200)

    def test_invalid_move_does_not_change_history(self):
        self.register('alice')
        self.login('alice')
        game_id = self.new_game()
        self.move(game_id, -1)
        self.assertEqual(self.record(game_id)[0], '[]')
        self.move(game_id, 'nonsense')
        self.assertEqual(self.record(game_id)[0], '[]')

    def test_user_isolation(self):
        self.register('alice')
        self.login('alice')
        game_id = self.new_game()
        self.move(game_id, 3)
        before = self.record(game_id)
        self.logout()
        self.register('bob')
        self.login('bob')
        self.assertNotIn(b'Game #', self.client.get('/dashboard').data)
        self.assertEqual(self.client.get(f'/games/{game_id}').status_code, 404)
        self.assertEqual(self.client.get(f'/games/{game_id}/replay').status_code, 404)
        self.assertEqual(self.move(game_id, 4).status_code, 404)
        self.assertEqual(self.record(game_id), before)

    def test_csrf_required(self):
        self.register('alice')
        self.login('alice')
        self.assertEqual(self.client.post('/games').status_code, 400)

    def test_duplicate_username(self):
        self.register('alice')
        result = self.register('alice')
        self.assertIn(b'already exists', result.data)


if __name__ == '__main__':
    unittest.main()
