"""Tests for the Tkinter window in tictactoe.py.

They are skipped automatically when Tkinter or a display is not available
(for example on a server without a screen).
"""

from __future__ import annotations

import unittest

try:
    import tkinter as tk
except ImportError:  # Python was built without Tk support
    tk = None


class GuiTests(unittest.TestCase):
    def setUp(self):
        if tk is None:
            self.skipTest("tkinter is not installed")
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"no display available: {error}")
        self.root.withdraw()

        from tictactoe import TicTacToeApp

        self.app = TicTacToeApp(self.root, lang="en")

    def tearDown(self):
        self.root.destroy()

    def text(self, widget) -> str:
        return str(widget.cget("text"))

    def test_starts_against_the_computer(self):
        self.assertTrue(self.app.vs_computer)
        self.assertEqual(self.text(self.app.status_label), "Your turn (X)")
        self.assertEqual(self.text(self.app.score_label), "You: 0    Computer: 0    Draws: 0")

    def test_two_player_game(self):
        app = self.app
        app.mode_var.set("pvp")
        app.on_settings_changed()
        for index in (0, 3, 1, 4, 2):
            app.human_move(index)
        self.assertEqual(app.game.winner, "X")
        self.assertEqual(self.text(app.status_label), "X wins!")
        self.assertEqual(self.text(app.score_label), "X: 1    O: 0    Draws: 0")

    def test_computer_replies_after_the_player(self):
        app = self.app
        app.difficulty_var.set("hard")
        app.on_settings_changed()
        app.human_move(4)
        self.assertIsNotNone(app.pending_move)
        self.assertEqual(self.text(app.status_label), "Computer is thinking...")

        app.human_move(0)  # ignored: it is the computer's turn
        self.assertEqual(app.game.board.count("X"), 1)

        app._cancel_pending_move()
        app.computer_move()
        self.assertEqual(app.game.board.count("O"), 1)
        self.assertEqual(self.text(app.status_label), "Your turn (X)")

    def test_computer_starts_when_the_player_chooses_o(self):
        app = self.app
        app.human_var.set("O")
        app.on_settings_changed()
        self.assertIsNotNone(app.pending_move)
        app._cancel_pending_move()
        app.computer_move()
        self.assertEqual(app.game.board.count("X"), 1)
        self.assertEqual(self.text(app.status_label), "Your turn (O)")

    def test_language_switch(self):
        app = self.app
        app.lang_var.set("tr")
        app.apply_language()
        self.assertEqual(self.text(app.new_button), "Yeni oyun")
        self.assertEqual(self.text(app.status_label), "Sıra sende (X)")
        self.assertEqual(self.root.title(), "XOX (Tic-Tac-Toe)")


if __name__ == "__main__":
    unittest.main()
