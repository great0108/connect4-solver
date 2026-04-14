"""Connect 4 solver implementation.

This module provides a Python implementation of the C++ `Solver` class
from the reference Connect4 solver.
"""

from __future__ import annotations

from position import Position
from table import TranspositionTable


class Solver:
    def __init__(self) -> None:
        self.nodeCount = 0
        self.columnOrder = [Position.WIDTH // 2 + (1 - 2 * (i % 2)) * (i + 1) // 2 for i in range(Position.WIDTH)]
        self.transTable = TranspositionTable(8388593)

    def reset(self) -> None:
        self.nodeCount = 0
        self.transTable.reset()

    def solve(self, position: Position, weak: bool = False) -> int:
        self.nodeCount = 0
        if position.canWinNext():
            return (Position.WIDTH * Position.HEIGHT + 1 - position.nbMoves()) // 2

        minimum = -(Position.WIDTH * Position.HEIGHT - position.nbMoves()) // 2
        maximum = (Position.WIDTH * Position.HEIGHT + 1 - position.nbMoves()) // 2
        if weak:
            minimum = -1
            maximum = 1

        while minimum < maximum:
            med = minimum + (maximum - minimum) // 2
            if med <= 0 and minimum // 2 < med:
                med = minimum // 2
            elif med >= 0 and maximum // 2 > med:
                med = maximum // 2

            result = self._negamax(position, med, med + 1)
            if result <= med:
                maximum = result
            else:
                minimum = result

        return minimum

    def getNodeCount(self) -> int:
        return self.nodeCount

    def _negamax(self, position: Position, alpha: int, beta: int) -> int:
        self.nodeCount += 1
        assert not position.canWinNext()

        next_moves = position.possibleNonLoosingMoves()
        if next_moves == 0:
            return -(Position.WIDTH * Position.HEIGHT - position.nbMoves() - 1) // 2

        if position.nbMoves() >= Position.WIDTH * Position.HEIGHT - 2:
            return 0

        minimum = -(Position.WIDTH * Position.HEIGHT - 2 - position.nbMoves()) // 2
        if alpha < minimum:
            alpha = minimum
            if alpha >= beta:
                return alpha

        max_score = (Position.WIDTH * Position.HEIGHT - 1 - position.nbMoves()) // 2
        val = self.transTable.get(position.key())
        if val != 0:
            max_score = val + Position.MIN_SCORE - 1

        if beta > max_score:
            beta = max_score
            if alpha >= beta:
                return beta

        for x in range(Position.WIDTH):
            col = self.columnOrder[x]
            if next_moves & position.column_mask(col):
                next_position = position.copy()
                next_position.play(col)
                score = -self._negamax(next_position, -beta, -alpha)
                if score >= beta:
                    return score
                if score > alpha:
                    alpha = score

        self.transTable.put(position.key(), alpha - Position.MIN_SCORE + 1)
        return alpha


__all__ = ["Solver"]
