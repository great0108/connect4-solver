"""Simple transposition table implementation.

This module mirrors the behavior of the C++ TranspositionTable from the
Connect4 solver reference implementation.
"""

from __future__ import annotations


class TranspositionTable:
    def __init__(self, size: int) -> None:
        if size <= 0:
            raise ValueError("size must be positive")
        self._size = size
        self._table: list[tuple[int, int]] = [(0, 0)] * size

    def reset(self) -> None:
        """Empty the transposition table."""
        self._table = [(0, 0)] * self._size

    def _index(self, key: int) -> int:
        return key % self._size

    def put(self, key: int, val: int) -> None:
        """Store a non-zero 8-bit value for a 56-bit key."""
        i = self._index(key)
        self._table[i] = (key, val)

    def get(self, key: int) -> int:
        """Return the stored value for a key or 0 if the entry is missing."""
        i = self._index(key)
        stored_key, stored_val = self._table[i]
        if stored_key == key:
            return stored_val
        return 0


__all__ = ["TranspositionTable"]
