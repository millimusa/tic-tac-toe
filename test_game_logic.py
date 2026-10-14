"""Tests for game_logic.py. Run all tests with:  python -m unittest -v"""

from __future__ import annotations

import random
import unittest

from game_logic import (
    EMPTY,
    O,
    WIN_LINES,
    X,
    Game,
    available_moves,
    best_moves,
    choose_move,
    other,
    winner,
    winning_line,
)


def board(text: str) -> list[str]:
    """Build a board from 9 characters in reading order; "." is an empty cell."""
    assert len(text) == 9, text
    return [EMPTY if char == "." else char for char in text]


class BoardTests(unittest.TestCase):
    def test_every_line_is_detected(self):
        for line in WIN_LINES:
            for mark in (X, O):
                cells = [EMPTY] * 9
                for index in line:
                    cells[index] = mark
                with self.subTest(line=line, mark=mark):
                    self.assertEqual(winner(cells), mark)
                    self.assertEqual(winning_line(cells), line)

    def test_no_winner_on_empty_or_drawn_board(self):
        self.assertIsNone(winner(board(".........")))
        self.assertIsNone(winner(board("XOXXOOOXX")))

    def test_available_moves(self):
        self.assertEqual(available_moves(board("X.O.X.O..")), [1, 3, 5, 7, 8])

    def test_other(self):
        self.assertEqual(other(X), O)
        self.assertEqual(other(O), X)
        with self.assertRaises(ValueError):
            other("Z")


class GameTests(unittest.TestCase):
    def test_players_take_turns(self):
        game = Game()
        self.assertEqual(game.current, X)
        game.play(4)
        self.assertEqual(game.board[4], X)
        self.assertEqual(game.current, O)
        game.play(0)
        self.assertEqual(game.board[0], O)
        self.assertEqual(game.current, X)

    def test_o_can_start(self):
        self.assertEqual(Game(first_player=O).current, O)

    def test_invalid_moves_are_rejected(self):
        game = Game()
        game.play(0)
        for index in (0, 9, -1):
            with self.subTest(index=index), self.assertRaises(ValueError):
                game.play(index)
        self.assertEqual(game.board.count(EMPTY), 8)

    def test_win_ends_the_game(self):
        game = Game()
        for index in (0, 3, 1, 4, 2):  # X takes the top row
            game.play(index)
        self.assertEqual(game.winner, X)
        self.assertEqual(game.win_line, (0, 1, 2))
        self.assertTrue(game.is_over)
        self.assertFalse(game.is_draw)
        with self.assertRaises(ValueError):
            game.play(8)

    def test_full_board_without_line_is_a_draw(self):
        game = Game()
        for index in (0, 1, 2, 4, 3, 5, 7, 6, 8):
            game.play(index)
        self.assertIsNone(game.winner)
        self.assertTrue(game.is_draw)
        self.assertTrue(game.is_over)

    def test_reset_starts_a_new_game(self):
        game = Game()
        for index in (0, 3, 1, 4, 2):
            game.play(index)
        game.reset(first_player=O)
        self.assertEqual(game.board, [EMPTY] * 9)
        self.assertEqual(game.current, O)
        self.assertIsNone(game.winner)
        self.assertIsNone(game.win_line)
        self.assertFalse(game.is_over)


class ComputerTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(2026)

    def test_takes_a_winning_move(self):
        cells = board("XX.OO....")
        for level in ("medium", "hard"):
            with self.subTest(level=level):
                self.assertEqual(choose_move(cells, X, level, self.rng), 2)

    def test_blocks_the_opponent(self):
        cells = board("XX..O....")
        for level in ("medium", "hard"):
            with self.subTest(level=level):
                self.assertEqual(choose_move(cells, O, level, self.rng), 2)

    def test_hard_answers_a_corner_opening_with_the_centre(self):
        # Every other reply to a corner opening loses against perfect play.
        self.assertEqual(best_moves(board("X........"), O), [4])

    def test_easy_always_returns_a_legal_move(self):
        cells = board("XOX.O.X..")
        for _ in range(100):
            self.assertIn(choose_move(cells, O, "easy", self.rng), available_moves(cells))

    def test_errors(self):
        with self.assertRaises(ValueError):
            choose_move(board("........."), X, "impossible")
        with self.assertRaises(ValueError):
            choose_move(board("XXXOO...."), O, "hard")
        with self.assertRaises(ValueError):
            choose_move(board("XOXXOOOXX"), X, "easy")

    def _assert_never_loses(self, cells: list[str], to_move: str, computer: str) -> None:
        result = winner(cells)
        if result is not None:
            self.assertEqual(result, computer, "the computer lost: " + "".join(cells))
            return
        if EMPTY not in cells:
            return
        if to_move == computer:
            moves = best_moves(cells, computer)  # every move the computer might pick
        else:
            moves = available_moves(cells)  # every possible reply of the opponent
        for index in moves:
            cells[index] = to_move
            self._assert_never_loses(cells, other(to_move), computer)
            cells[index] = EMPTY

    def test_hard_never_loses(self):
        """Try every possible opponent against every optimal computer choice."""
        for computer in (X, O):
            with self.subTest(computer=computer):
                self._assert_never_loses([EMPTY] * 9, X, computer)

    def test_two_hard_players_always_draw(self):
        for seed in range(20):
            rng = random.Random(seed)
            game = Game()
            while not game.is_over:
                game.play(choose_move(game.board, game.current, "hard", rng))
            with self.subTest(seed=seed):
                self.assertTrue(game.is_draw)


if __name__ == "__main__":
    unittest.main()
