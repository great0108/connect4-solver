"""Connect 4 solver implementation.

This module provides a Python implementation of the C++ `Solver` class
from the reference Connect4 solver.
"""

from __future__ import annotations

from position import Position


class Solver:
    def __init__(self) -> None:
        self.nodeCount = 0
        self.columnOrder = [Position.WIDTH // 2 + (1 - 2 * (i % 2)) * (i + 1) // 2 for i in range(Position.WIDTH)]

    def solve(self, position: Position) -> int:
        self.nodeCount = 0
        alpha = -Position.WIDTH * Position.HEIGHT // 2
        beta = Position.WIDTH * Position.HEIGHT // 2
        return self._negamax(position, alpha, beta)

    def getNodeCount(self) -> int:
        return self.nodeCount

    def _negamax(self, position: Position, alpha: int, beta: int) -> int:
        self.nodeCount += 1

        if position.nbMoves() == Position.WIDTH * Position.HEIGHT:
            return 0

        for x in range(Position.WIDTH):
            if position.canPlay(x) and position.isWinningMove(x):
                return (Position.WIDTH * Position.HEIGHT + 1 - position.nbMoves()) // 2

        max_score = (Position.WIDTH * Position.HEIGHT - 1 - position.nbMoves()) // 2
        if beta > max_score:
            beta = max_score
            if alpha >= beta:
                return beta

        for x in range(Position.WIDTH):
            if position.canPlay(self.columnOrder[x]):
                next_position = position.copy()
                next_position.play(self.columnOrder[x])
                score = -self._negamax(next_position, -beta, -alpha)
                if score >= beta:
                    return score
                if score > alpha:
                    alpha = score

        return alpha


__all__ = ["Solver"]
