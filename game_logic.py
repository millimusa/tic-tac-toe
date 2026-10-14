"""Rules of Tic-Tac-Toe and a computer opponent.

This module has no user-interface code, so the Tkinter window
(tictactoe.py) and the tests (test_game_logic.py) can both use it.

Board cells are numbered 0-8 in reading order:

     0 | 1 | 2
    ---+---+---
     3 | 4 | 5
    ---+---+---
     6 | 7 | 8
"""

from __future__ import annotations

import random
from functools import lru_cache
from typing import Optional, Sequence

X = "X"
O = "O"
EMPTY = " "

DIFFICULTIES = ("easy", "medium", "hard")

WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)

Board = Sequence[str]


def other(player: str) -> str:
    """Return the opponent of ``player``."""
    if player == X:
        return O
    if player == O:
        return X
    raise ValueError(f"Unknown player: {player!r}")


def winning_line(board: Board) -> Optional[tuple[int, int, int]]:
    """Return the three cells of a completed line, or ``None``."""
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return (a, b, c)
    return None


def winner(board: Board) -> Optional[str]:
    """Return ``X`` or ``O`` if that player has three in a row, else ``None``."""
    line = winning_line(board)
    return board[line[0]] if line else None


def available_moves(board: Board) -> list[int]:
    """Return the indexes of all empty cells."""
    return [index for index, cell in enumerate(board) if cell == EMPTY]


class Game:
    """One game: the board, whose turn it is and the result."""

    def __init__(self, first_player: str = X) -> None:
        self.reset(first_player)

    def reset(self, first_player: str = X) -> None:
        """Clear the board and give the first move to ``first_player``."""
        other(first_player)  # raises ValueError for anything but X or O
        self.board: list[str] = [EMPTY] * 9
        self.current: str = first_player
        self.winner: Optional[str] = None
        self.win_line: Optional[tuple[int, int, int]] = None

    @property
    def is_draw(self) -> bool:
        return self.winner is None and EMPTY not in self.board

    @property
    def is_over(self) -> bool:
        return self.winner is not None or EMPTY not in self.board

    def play(self, index: int) -> None:
        """Put the current player's mark on ``index`` and pass the turn."""
        if self.is_over:
            raise ValueError("The game is already over.")
        if not 0 <= index < 9:
            raise ValueError(f"Cell index must be between 0 and 8, got {index}.")
        if self.board[index] != EMPTY:
            raise ValueError(f"Cell {index} is already taken.")

        self.board[index] = self.current
        self.win_line = winning_line(self.board)
        if self.win_line:
            self.winner = self.current
        else:
            self.current = other(self.current)


@lru_cache(maxsize=None)
def _score(board: tuple[str, ...], player: str) -> int:
    """Minimax (negamax) value of ``board`` for ``player``, who moves next.

    A positive value means ``player`` can force a win, 0 means the game
    ends in a draw with best play, and a negative value means ``player``
    loses against best play. Quicker wins score higher and slower losses
    score less negative, so the computer wins as fast as it can and
    resists as long as it can. Results are cached, so even the first move
    on an empty board is instant.
    """
    if winner(board) is not None:
        # The opponent completed a line with the previous move.
        return -(1 + board.count(EMPTY))
    if EMPTY not in board:
        return 0
    opponent = other(player)
    return max(
        -_score(board[:index] + (player,) + board[index + 1:], opponent)
        for index in available_moves(board)
    )


def best_moves(board: Board, player: str) -> list[int]:
    """Return every move that is optimal for ``player`` (perfect play)."""
    state = tuple(board)
    if winner(state) is not None:
        return []
    opponent = other(player)
    scores = {
        index: -_score(state[:index] + (player,) + state[index + 1:], opponent)
        for index in available_moves(state)
    }
    if not scores:
        return []
    best = max(scores.values())
    return [index for index, score in scores.items() if score == best]


def choose_move(
    board: Board,
    player: str,
    difficulty: str = "hard",
    rng: Optional[random.Random] = None,
) -> int:
    """Choose the computer's move for ``player``.

    easy   -- a random empty cell
    medium -- wins if it can, otherwise blocks the opponent's winning
              move, otherwise plays randomly (it can be beaten with a fork)
    hard   -- perfect play with minimax; it never loses
    """
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Unknown difficulty: {difficulty!r}")
    moves = available_moves(board)
    if winner(board) is not None or not moves:
        raise ValueError("The game is already over.")
    rng = rng or random.Random()

    if difficulty == "easy":
        return rng.choice(moves)

    if difficulty == "medium":
        for mark in (player, other(player)):  # first try to win, then block
            for index in moves:
                trial = list(board)
                trial[index] = mark
                if winner(trial) == mark:
                    return index
        return rng.choice(moves)

    return rng.choice(best_moves(board, player))
