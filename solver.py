"""Connect 4 solver implementation.

This module provides a Python implementation of the C++ `Solver` class
from the reference Connect4 solver.
"""

from __future__ import annotations

from position import Position


class Solver:
    def __init__(self) -> None:
        self.nodeCount = 0

    def solve(self, position: Position) -> int:
        self.nodeCount = 0
        return self._negamax(position)

    def getNodeCount(self) -> int:
        return self.nodeCount

    def _negamax(self, position: Position) -> int:
        self.nodeCount += 1

        if position.nbMoves() == Position.WIDTH * Position.HEIGHT:
            return 0

        for x in range(Position.WIDTH):
            if position.canPlay(x) and position.isWinningMove(x):
                return (Position.WIDTH * Position.HEIGHT + 1 - position.nbMoves()) // 2

        bestScore = -Position.WIDTH * Position.HEIGHT
        for x in range(Position.WIDTH):
            if position.canPlay(x):
                next_position = position.copy()
                next_position.play(x)
                score = -self._negamax(next_position)
                if score > bestScore:
                    bestScore = score

        return bestScore


__all__ = ["Solver"]
