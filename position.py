"""Connect 4 position model.

This module provides a Python implementation of the C++ `Position` class
from the reference Connect4 solver.
"""

from __future__ import annotations


class Position:
    WIDTH = 7
    HEIGHT = 6
    HEIGHT1 = HEIGHT + 1
    HEIGHT2 = HEIGHT + 2
    MIN_SCORE = -WIDTH * HEIGHT // 2 + 3
    MAX_SCORE = (WIDTH * HEIGHT + 1) // 2 - 3

    def __init__(self) -> None:
        self.current_position = 0
        self.mask = 0
        self.moves = 0
        self._winning_position = 0

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
        self._winning_position = self.compute_winning_position(self.current_position, self.mask)

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
        clone._winning_position = self._winning_position
        return clone

    def key(self) -> int:
        return self.current_position + self.mask

    def winning_position(self) -> int:
        return self._winning_position

    def opponent_winning_position(self) -> int:
        return self.compute_winning_position(self.current_position ^ self.mask, self.mask)

    def moveScore(self, move: int) -> int:
        return self.compute_winning_position(self.current_position | move, self.mask).bit_count()

    def possible(self) -> int:
        return (self.mask + Position.BOTTOM_MASK_ALL) & Position.BOARD_MASK

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
        h = Position.HEIGHT
        h1 = Position.HEIGHT1
        h2 = Position.HEIGHT2

        r = (position << 1) & (position << 2) & (position << 3)

        p = (position << h1) & (position << (2 * h1))
        r |= p & (position << (3 * h1))
        r |= p & (position >> h1)
        p = (position >> h1) & (position >> (2 * h1))
        r |= p & (position << h1)
        r |= p & (position >> (3 * h1))

        p = (position << h) & (position << (2 * h))
        r |= p & (position << (3 * h))
        r |= p & (position >> h)
        p = (position >> h) & (position >> (2 * h))
        r |= p & (position << h)
        r |= p & (position >> (3 * h))

        p = (position << h2) & (position << (2 * h2))
        r |= p & (position << (3 * h2))
        r |= p & (position >> h2)
        p = (position >> h2) & (position >> (2 * h2))
        r |= p & (position << h2)
        r |= p & (position >> (3 * h2))

        return r & (Position.BOARD_MASK ^ mask)

    @staticmethod
    def bottom_mask_all() -> int:
        return Position.BOTTOM_MASK_ALL

    @staticmethod
    def board_mask() -> int:
        return Position.BOARD_MASK

    @staticmethod
    def alignment(pos: int) -> bool:
        h = Position.HEIGHT
        h1 = Position.HEIGHT1
        h2 = Position.HEIGHT2

        m = pos & (pos >> h1)
        if m & (m >> (2 * h1)):
            return True

        m = pos & (pos >> h)
        if m & (m >> (2 * h)):
            return True

        m = pos & (pos >> h2)
        if m & (m >> (2 * h2)):
            return True

        m = pos & (pos >> 1)
        if m & (m >> 2):
            return True

        return False

    @staticmethod
    def top_mask(col: int) -> int:
        return Position.TOP_MASKS[col]

    @staticmethod
    def bottom_mask(col: int) -> int:
        return Position.BOTTOM_MASKS[col]

    @staticmethod
    def column_mask(col: int) -> int:
        return Position.COLUMN_MASKS[col]


Position.TOP_MASKS = [
    (1 << (Position.HEIGHT - 1)) << (col * (Position.HEIGHT + 1))
    for col in range(Position.WIDTH)
]
Position.BOTTOM_MASKS = [
    1 << (col * (Position.HEIGHT + 1))
    for col in range(Position.WIDTH)
]
Position.COLUMN_MASKS = [
    ((1 << Position.HEIGHT) - 1) << (col * (Position.HEIGHT + 1))
    for col in range(Position.WIDTH)
]
Position.BOTTOM_MASK_ALL = sum(Position.BOTTOM_MASKS)
Position.BOARD_MASK = Position.BOTTOM_MASK_ALL * ((1 << Position.HEIGHT) - 1)

__all__ = ["Position"]
