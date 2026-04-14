"""Connect 4 position model.

This module provides a Python implementation of the C++ `Position` class
from the reference Connect4 solver.
"""

from __future__ import annotations


class Position:
    WIDTH = 7
    HEIGHT = 6
    MIN_SCORE = -WIDTH * HEIGHT // 2 + 3
    MAX_SCORE = (WIDTH * HEIGHT + 1) // 2 - 3

    def __init__(self) -> None:
        self.current_position = 0
        self.mask = 0
        self.moves = 0

    def canPlay(self, col: int) -> bool:
        return 0 <= col < Position.WIDTH and (self.mask & self.top_mask(col)) == 0

    def play(self, col: int | str) -> None | int:
        if isinstance(col, str):
            return self.play_sequence(col)

        if not self.canPlay(col):
            raise ValueError(f"Cannot play column {col}")

        self.current_position ^= self.mask
        self.mask |= self.mask + self.bottom_mask(col)
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

        pos = self.current_position
        pos |= (self.mask + self.bottom_mask(col)) & self.column_mask(col)
        return self.alignment(pos)

    def nbMoves(self) -> int:
        return self.moves

    def copy(self) -> Position:
        clone = Position()
        clone.current_position = self.current_position
        clone.mask = self.mask
        clone.moves = self.moves
        return clone

    def key(self) -> int:
        return self.current_position + self.mask

    def winning_position(self) -> int:
        return self.compute_winning_position(self.current_position, self.mask)

    def opponent_winning_position(self) -> int:
        return self.compute_winning_position(self.current_position ^ self.mask, self.mask)

    def possible(self) -> int:
        return (self.mask + self.bottom_mask_all()) & self.board_mask()

    def canWinNext(self) -> bool:
        return bool(self.winning_position() & self.possible())

    def possibleNonLoosingMoves(self) -> int:
        assert not self.canWinNext()
        possible_mask = self.possible()
        opponent_win = self.opponent_winning_position()
        forced_moves = possible_mask & opponent_win
        if forced_moves:
            if forced_moves & (forced_moves - 1):
                return 0
            possible_mask = forced_moves
        return possible_mask & ~(opponent_win >> 1)

    @staticmethod
    def compute_winning_position(position: int, mask: int) -> int:
        r = (position << 1) & (position << 2) & (position << 3)

        p = (position << (Position.HEIGHT + 1)) & (position << 2 * (Position.HEIGHT + 1))
        r |= p & (position << 3 * (Position.HEIGHT + 1))
        r |= p & (position >> (Position.HEIGHT + 1))
        p = (position >> (Position.HEIGHT + 1)) & (position >> 2 * (Position.HEIGHT + 1))
        r |= p & (position << (Position.HEIGHT + 1))
        r |= p & (position >> 3 * (Position.HEIGHT + 1))

        p = (position << Position.HEIGHT) & (position << 2 * Position.HEIGHT)
        r |= p & (position << 3 * Position.HEIGHT)
        r |= p & (position >> Position.HEIGHT)
        p = (position >> Position.HEIGHT) & (position >> 2 * Position.HEIGHT)
        r |= p & (position << Position.HEIGHT)
        r |= p & (position >> 3 * Position.HEIGHT)

        p = (position << (Position.HEIGHT + 2)) & (position << 2 * (Position.HEIGHT + 2))
        r |= p & (position << 3 * (Position.HEIGHT + 2))
        r |= p & (position >> (Position.HEIGHT + 2))
        p = (position >> (Position.HEIGHT + 2)) & (position >> 2 * (Position.HEIGHT + 2))
        r |= p & (position << (Position.HEIGHT + 2))
        r |= p & (position >> 3 * (Position.HEIGHT + 2))

        return r & (Position.board_mask() ^ mask)

    @staticmethod
    def bottom_mask_all() -> int:
        return sum(1 << (col * (Position.HEIGHT + 1)) for col in range(Position.WIDTH))

    @staticmethod
    def board_mask() -> int:
        return Position.bottom_mask_all() * ((1 << Position.HEIGHT) - 1)

    @staticmethod
    def alignment(pos: int) -> bool:
        m = pos & (pos >> (Position.HEIGHT + 1))
        if m & (m >> (2 * (Position.HEIGHT + 1))):
            return True

        m = pos & (pos >> Position.HEIGHT)
        if m & (m >> (2 * Position.HEIGHT)):
            return True

        m = pos & (pos >> (Position.HEIGHT + 2))
        if m & (m >> (2 * (Position.HEIGHT + 2))):

            return True

        m = pos & (pos >> 1)
        if m & (m >> 2):
            return True

        return False

    @staticmethod
    def top_mask(col: int) -> int:
        return (1 << (Position.HEIGHT - 1)) << (col * (Position.HEIGHT + 1))

    @staticmethod
    def bottom_mask(col: int) -> int:
        return 1 << (col * (Position.HEIGHT + 1))

    @staticmethod
    def column_mask(col: int) -> int:
        return ((1 << Position.HEIGHT) - 1) << (col * (Position.HEIGHT + 1))


__all__ = ["Position"]
