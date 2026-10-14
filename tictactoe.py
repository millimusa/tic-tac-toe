"""Tic-Tac-Toe (XOX) with a Tkinter graphical interface.

Start the game with:

    python tictactoe.py              # Turkish interface
    python tictactoe.py --lang en    # English interface

Only the Python standard library is used. The rules and the computer
opponent live in game_logic.py; this file contains the window.
"""

from __future__ import annotations

import argparse
import math
import random
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Callable, Optional

from game_logic import EMPTY, O, X, Game, choose_move, other

COMPUTER_DELAY_MS = 450  # short pause so the computer's move is easy to follow

TEXTS = {
    "tr": {
        "title": "XOX (Tic-Tac-Toe)",
        "settings": "Ayarlar",
        "mode": "Mod:",
        "pvp": "İki oyuncu",
        "pvc": "Bilgisayara karşı",
        "difficulty": "Zorluk:",
        "easy": "Kolay",
        "medium": "Orta",
        "hard": "Zor",
        "you_play": "İşaretin:",
        "language": "Dil:",
        "new_game": "Yeni oyun",
        "reset_score": "Skoru sıfırla",
        "turn": "Sıra: {player}",
        "your_turn": "Sıra sende ({player})",
        "thinking": "Bilgisayar düşünüyor...",
        "wins": "{player} kazandı!",
        "you_win": "Tebrikler, kazandın!",
        "computer_wins": "Bilgisayar kazandı!",
        "draw": "Berabere!",
        "score_pvp": "X: {x}    O: {o}    Berabere: {draws}",
        "score_pvc": "Sen: {you}    Bilgisayar: {computer}    Berabere: {draws}",
        "hint": "1-9 tuşları hücre seçer (sol üstten başlar), N yeni oyun başlatır.",
    },
    "en": {
        "title": "Tic-Tac-Toe",
        "settings": "Settings",
        "mode": "Mode:",
        "pvp": "Two players",
        "pvc": "Versus computer",
        "difficulty": "Difficulty:",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
        "you_play": "You play:",
        "language": "Language:",
        "new_game": "New game",
        "reset_score": "Reset score",
        "turn": "Turn: {player}",
        "your_turn": "Your turn ({player})",
        "thinking": "Computer is thinking...",
        "wins": "{player} wins!",
        "you_win": "Congratulations, you win!",
        "computer_wins": "The computer wins!",
        "draw": "It's a draw!",
        "score_pvp": "X: {x}    O: {o}    Draws: {draws}",
        "score_pvc": "You: {you}    Computer: {computer}    Draws: {draws}",
        "hint": "Keys 1-9 pick a cell (starting top left), N starts a new game.",
    },
}

LANGUAGE_NAMES = {"tr": "Türkçe", "en": "English"}


class TicTacToeApp:
    """The game window: settings, board, status line and score."""

    CELL = 120  # size of one board cell in pixels
    PAD = 28    # space between a mark and the edge of its cell
    BOARD_BG = "#ffffff"
    GRID_COLOR = "#334155"
    COLORS = {X: "#2563eb", O: "#dc2626"}
    PREVIEW_COLORS = {X: "#c7d7fb", O: "#f6c6c6"}
    WIN_CELL_BG = "#fef3c7"
    WIN_LINE_COLOR = "#16a34a"
    DRAW_COLOR = "#475569"

    def __init__(self, root: tk.Tk, lang: str = "tr") -> None:
        if lang not in TEXTS:
            raise ValueError(f"Unsupported language: {lang!r}")
        self.root = root
        self.game = Game()
        self.rng = random.Random()
        self.scores = {X: 0, O: 0, "draw": 0}
        self.pending_move: Optional[str] = None  # id of a scheduled computer move
        self.hover_cell: Optional[int] = None

        self.lang_var = tk.StringVar(master=root, value=lang)
        self.mode_var = tk.StringVar(master=root, value="pvc")
        self.difficulty_var = tk.StringVar(master=root, value="medium")
        self.human_var = tk.StringVar(master=root, value=X)
        self._settings = self._current_settings()

        self._setup_style()
        self._build_widgets()
        self.root.bind("<Key>", self.on_key)
        self.apply_language()
        self._update_controls()
        self.new_game()

    # ------------------------------------------------------------------
    # Window layout
    # ------------------------------------------------------------------
    def _setup_style(self) -> None:
        style = ttk.Style(self.root)
        # Linux starts with the plain "default" theme; "clam" looks more modern.
        if style.theme_use() == "default" and "clam" in style.theme_names():
            style.theme_use("clam")
        self.title_font = tkfont.Font(root=self.root, font="TkDefaultFont")
        self.title_font.configure(size=18, weight="bold")
        self.status_font = tkfont.Font(root=self.root, font="TkDefaultFont")
        self.status_font.configure(size=13, weight="bold")

    def _build_widgets(self) -> None:
        self.root.resizable(False, False)
        outer = ttk.Frame(self.root, padding=16)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)

        self.title_label = ttk.Label(outer, font=self.title_font)
        self.title_label.grid(row=0, column=0, pady=(0, 10))

        self.settings_frame = ttk.LabelFrame(outer, padding=(12, 6))
        self.settings_frame.grid(row=1, column=0, sticky="ew")
        changed = self.on_settings_changed
        self.mode_caption, self.mode_buttons = self._radio_row(
            0, self.mode_var, ("pvp", "pvc"), changed)
        self.difficulty_caption, self.difficulty_buttons = self._radio_row(
            1, self.difficulty_var, ("easy", "medium", "hard"), changed)
        self.human_caption, self.human_buttons = self._radio_row(
            2, self.human_var, (X, O), changed, labels={X: X, O: O})
        self.language_caption, _ = self._radio_row(
            3, self.lang_var, tuple(LANGUAGE_NAMES), self.apply_language,
            labels=LANGUAGE_NAMES)

        size = 3 * self.CELL
        self.canvas = tk.Canvas(outer, width=size, height=size, bg=self.BOARD_BG,
                                highlightthickness=0, cursor="hand2")
        self.canvas.grid(row=2, column=0, pady=14)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", self.on_leave)

        self.status_label = ttk.Label(outer, font=self.status_font, anchor="center")
        self.status_label.grid(row=3, column=0, sticky="ew")
        self.score_label = ttk.Label(outer, anchor="center")
        self.score_label.grid(row=4, column=0, sticky="ew", pady=(4, 10))

        buttons = ttk.Frame(outer)
        buttons.grid(row=5, column=0)
        self.new_button = ttk.Button(buttons, command=self.new_game)
        self.new_button.grid(row=0, column=0, padx=4)
        self.reset_button = ttk.Button(buttons, command=self.reset_score)
        self.reset_button.grid(row=0, column=1, padx=4)

        self.hint_label = ttk.Label(outer, foreground="#64748b", justify="center",
                                    wraplength=size)
        self.hint_label.grid(row=6, column=0, pady=(10, 0))

    def _radio_row(
        self,
        row: int,
        variable: tk.StringVar,
        values: tuple[str, ...],
        command: Callable[[], None],
        labels: Optional[dict[str, str]] = None,
    ) -> tuple[ttk.Label, dict[str, ttk.Radiobutton]]:
        """Add one settings row: a caption followed by radio buttons."""
        caption = ttk.Label(self.settings_frame)
        caption.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)
        buttons = {}
        for column, value in enumerate(values, start=1):
            button = ttk.Radiobutton(self.settings_frame, variable=variable,
                                     value=value, command=command)
            if labels:
                button.configure(text=labels[value])
            button.grid(row=row, column=column, sticky="w", padx=(0, 12), pady=2)
            buttons[value] = button
        return caption, buttons

    # ------------------------------------------------------------------
    # Texts and settings
    # ------------------------------------------------------------------
    def t(self, key: str, **values: object) -> str:
        """Return the text for ``key`` in the selected language."""
        return TEXTS[self.lang_var.get()][key].format(**values)

    def apply_language(self) -> None:
        """Show every text in the selected language."""
        self.root.title(self.t("title"))
        self.title_label.configure(text=self.t("title"))
        self.settings_frame.configure(text=self.t("settings"))
        self.mode_caption.configure(text=self.t("mode"))
        self.difficulty_caption.configure(text=self.t("difficulty"))
        self.human_caption.configure(text=self.t("you_play"))
        self.language_caption.configure(text=self.t("language"))
        for value, button in {**self.mode_buttons, **self.difficulty_buttons}.items():
            button.configure(text=self.t(value))
        self.new_button.configure(text=self.t("new_game"))
        self.reset_button.configure(text=self.t("reset_score"))
        self.hint_label.configure(text=self.t("hint"))
        self.update_status()
        self.update_score()

    def _current_settings(self) -> tuple[str, str, str]:
        return (self.mode_var.get(), self.difficulty_var.get(), self.human_var.get())

    def on_settings_changed(self) -> None:
        """A new mode, difficulty or mark starts a fresh game and score."""
        settings = self._current_settings()
        if settings == self._settings:
            return
        self._settings = settings
        self._update_controls()
        self.reset_score()
        self.new_game()

    def _update_controls(self) -> None:
        """Difficulty and mark only matter when playing against the computer."""
        state = "!disabled" if self.vs_computer else "disabled"
        widgets = [self.difficulty_caption, self.human_caption,
                   *self.difficulty_buttons.values(), *self.human_buttons.values()]
        for widget in widgets:
            widget.state([state])

    @property
    def vs_computer(self) -> bool:
        return self.mode_var.get() == "pvc"

    @property
    def human(self) -> str:
        return self.human_var.get()

    @property
    def computer(self) -> str:
        return other(self.human)

    # ------------------------------------------------------------------
    # Game flow
    # ------------------------------------------------------------------
    def is_human_turn(self) -> bool:
        if self.game.is_over or self.pending_move is not None:
            return False
        return not self.vs_computer or self.game.current == self.human

    def new_game(self) -> None:
        """Clear the board. X always starts, so the computer moves first if it is X."""
        self._cancel_pending_move()
        self.game.reset(first_player=X)
        self._schedule_computer_move()
        self.draw_board()
        self.update_status()

    def reset_score(self) -> None:
        self.scores = {X: 0, O: 0, "draw": 0}
        self.update_score()

    def human_move(self, index: int) -> None:
        if not self.is_human_turn() or self.game.board[index] != EMPTY:
            return
        self.game.play(index)
        self._after_move()

    def computer_move(self) -> None:
        self.pending_move = None
        if self.game.is_over:
            return
        index = choose_move(self.game.board, self.game.current,
                            self.difficulty_var.get(), self.rng)
        self.game.play(index)
        self._after_move()

    def _after_move(self) -> None:
        if self.game.is_over:
            self.scores[self.game.winner or "draw"] += 1
            self.update_score()
        else:
            self._schedule_computer_move()
        self.draw_board()
        self.update_status()

    def _schedule_computer_move(self) -> None:
        if (self.vs_computer and not self.game.is_over
                and self.game.current == self.computer):
            self.pending_move = self.root.after(COMPUTER_DELAY_MS, self.computer_move)

    def _cancel_pending_move(self) -> None:
        if self.pending_move is not None:
            self.root.after_cancel(self.pending_move)
            self.pending_move = None

    # ------------------------------------------------------------------
    # Status line and score
    # ------------------------------------------------------------------
    def update_status(self) -> None:
        game = self.game
        if game.winner:
            color = self.COLORS[game.winner]
            if not self.vs_computer:
                text = self.t("wins", player=game.winner)
            elif game.winner == self.human:
                text = self.t("you_win")
            else:
                text = self.t("computer_wins")
        elif game.is_draw:
            text, color = self.t("draw"), self.DRAW_COLOR
        else:
            color = self.COLORS[game.current]
            if self.pending_move is not None:
                text = self.t("thinking")
            elif self.vs_computer:
                text = self.t("your_turn", player=game.current)
            else:
                text = self.t("turn", player=game.current)
        self.status_label.configure(text=text, foreground=color)

    def update_score(self) -> None:
        if self.vs_computer:
            text = self.t("score_pvc", you=self.scores[self.human],
                          computer=self.scores[self.computer],
                          draws=self.scores["draw"])
        else:
            text = self.t("score_pvp", x=self.scores[X], o=self.scores[O],
                          draws=self.scores["draw"])
        self.score_label.configure(text=text)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _cell_origin(self, index: int) -> tuple[int, int]:
        return (index % 3) * self.CELL, (index // 3) * self.CELL

    def _cell_center(self, index: int) -> tuple[float, float]:
        x, y = self._cell_origin(index)
        return x + self.CELL / 2, y + self.CELL / 2

    def _cell_at(self, x: int, y: int) -> Optional[int]:
        column, row = x // self.CELL, y // self.CELL
        if 0 <= column < 3 and 0 <= row < 3:
            return int(row * 3 + column)
        return None

    def draw_board(self) -> None:
        canvas, cell = self.canvas, self.CELL
        size = 3 * cell
        canvas.delete("all")
        line = self.game.win_line

        if line:  # light background behind the winning cells
            for index in line:
                x, y = self._cell_origin(index)
                canvas.create_rectangle(x, y, x + cell, y + cell,
                                        fill=self.WIN_CELL_BG, width=0)

        for k in (1, 2):  # the four grid lines
            p = k * cell
            canvas.create_line(p, 12, p, size - 12, fill=self.GRID_COLOR,
                               width=4, capstyle=tk.ROUND)
            canvas.create_line(12, p, size - 12, p, fill=self.GRID_COLOR,
                               width=4, capstyle=tk.ROUND)

        for index, mark in enumerate(self.game.board):
            if mark != EMPTY:
                self._draw_mark(index, mark, self.COLORS[mark])

        hover = self.hover_cell  # faint preview of the next move under the mouse
        if hover is not None and self.is_human_turn() and self.game.board[hover] == EMPTY:
            mark = self.game.current
            self._draw_mark(hover, mark, self.PREVIEW_COLORS[mark])

        if line:  # strike through the three in a row
            (x1, y1), (x2, y2) = self._cell_center(line[0]), self._cell_center(line[2])
            length = math.hypot(x2 - x1, y2 - y1)
            dx, dy = (x2 - x1) / length * 30, (y2 - y1) / length * 30
            canvas.create_line(x1 - dx, y1 - dy, x2 + dx, y2 + dy,
                               fill=self.WIN_LINE_COLOR, width=10, capstyle=tk.ROUND)

    def _draw_mark(self, index: int, mark: str, color: str) -> None:
        x, y = self._cell_origin(index)
        near, far = self.PAD, self.CELL - self.PAD
        if mark == X:
            self.canvas.create_line(x + near, y + near, x + far, y + far,
                                    fill=color, width=10, capstyle=tk.ROUND)
            self.canvas.create_line(x + far, y + near, x + near, y + far,
                                    fill=color, width=10, capstyle=tk.ROUND)
        else:
            self.canvas.create_oval(x + near, y + near, x + far, y + far,
                                    outline=color, width=10)

    # ------------------------------------------------------------------
    # Mouse and keyboard
    # ------------------------------------------------------------------
    def on_click(self, event: tk.Event) -> None:
        index = self._cell_at(event.x, event.y)
        if index is not None:
            self.human_move(index)

    def on_motion(self, event: tk.Event) -> None:
        index = self._cell_at(event.x, event.y)
        if index != self.hover_cell:
            self.hover_cell = index
            self.draw_board()

    def on_leave(self, _event: tk.Event) -> None:
        if self.hover_cell is not None:
            self.hover_cell = None
            self.draw_board()

    def on_key(self, event: tk.Event) -> None:
        if event.char and event.char in "123456789":
            self.human_move(int(event.char) - 1)
        elif event.char in ("n", "N"):
            self.new_game()


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Tic-Tac-Toe (XOX) with a Tkinter window.")
    parser.add_argument("--lang", choices=sorted(TEXTS), default="tr",
                        help="interface language (default: tr)")
    args = parser.parse_args(argv)

    root = tk.Tk()
    TicTacToeApp(root, lang=args.lang)
    root.mainloop()


if __name__ == "__main__":
    main()
