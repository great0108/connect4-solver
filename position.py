"""Connect 4 position model.

This module provides a Python implementation of the C++ `Position` class
from the reference Connect4 solver.
"""

from __future__ import annotations


class Position:
    WIDTH = 7
    HEIGHT = 6

    def __init__(self) -> None:
        self.board = [[0] * Position.HEIGHT for _ in range(Position.WIDTH)]
        self.height = [0] * Position.WIDTH
        self.moves = 0

    def canPlay(self, col: int) -> bool:
        return 0 <= col < Position.WIDTH and self.height[col] < Position.HEIGHT

    def play(self, col: int | str) -> None | int:
        if isinstance(col, str):
            return self.play_sequence(col)

        if not self.canPlay(col):
            raise ValueError(f"Cannot play column {col}")
        self.board[col][self.height[col]] = 1 + self.moves % 2
        self.height[col] += 1
        self.moves += 1

    def play_sequence(self, seq: str) -> int:
        for i, ch in enumerate(seq):
            if not ch.isdigit():
                return i
            col = ord(ch) - ord("1")
            if col < 0 or col >= Position.WIDTH or not self.canPlay(col) or self.isWinningMove(col):
                return i
            self.play(col)
        return len(seq)

    def isWinningMove(self, col: int) -> bool:
        if not self.canPlay(col):
            raise ValueError(f"Column {col} is not playable")

        current_player = 1 + self.moves % 2

        if self.height[col] >= 3:
            if (
                self.board[col][self.height[col] - 1] == current_player
                and self.board[col][self.height[col] - 2] == current_player
                and self.board[col][self.height[col] - 3] == current_player
            ):
                return True

        for dy in (-1, 0, 1):
            nb = 0
            for dx in (-1, 1):
                x = col + dx
                y = self.height[col] + dx * dy
                while 0 <= x < Position.WIDTH and 0 <= y < Position.HEIGHT and self.board[x][y] == current_player:
                    nb += 1
                    x += dx
                    y += dx * dy
            if nb >= 3:
                return True

        return False

    def nbMoves(self) -> int:
        return self.moves

    def copy(self) -> "Position":
        clone = Position()
        for col in range(Position.WIDTH):
            clone.board[col] = self.board[col].copy()
            clone.height[col] = self.height[col]
        clone.moves = self.moves
        return clone


__all__ = ["Position"]
