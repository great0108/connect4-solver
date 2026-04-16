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
        self.root_move = -1
        self.columnOrder = [Position.WIDTH // 2 + (1 - 2 * (i % 2)) * (i + 1) // 2 for i in range(Position.WIDTH)]
        # self.transTable = TranspositionTable(8388593)
        self.transTable = TranspositionTable(838889)

    def reset(self) -> None:
        self.nodeCount = 0
        self.root_move = -1
        self.transTable.reset()

    def solve(self, position: Position, return_move: bool = False) -> int | tuple[int, int]:
        self.nodeCount = 0
        self.root_move = -1
        if position.canWinNext():
            score = (Position.WIDTH * Position.HEIGHT + 1 - position.nbMoves()) // 2
            if return_move:
                for col in range(Position.WIDTH):
                    if position.isWinningMove(col):
                        return score, col

            return score

        minimum = -((Position.WIDTH * Position.HEIGHT - position.nbMoves()) // 2)
        maximum = (Position.WIDTH * Position.HEIGHT + 1 - position.nbMoves()) // 2

        while minimum < maximum:
            med = minimum + (maximum - minimum) // 2
            if med <= 0 and minimum // 2 < med:
                med = minimum // 2
            elif med >= 0 and maximum // 2 > med:
                med = maximum // 2

            result = self._negamax(position, med, med + 1, root=return_move)
            if result <= med:
                maximum = result
            else:
                minimum = result

        if return_move:
            if self.root_move == -1:
                next_moves = position.possibleNonLoosingMoves()
                if next_moves == 0:
                    return -((Position.WIDTH * Position.HEIGHT - position.nbMoves()) // 2), 0
                print("Warning: root move not found")
                return minimum, self.solve(position)
            return minimum, self.root_move
        return minimum

                

    def getNodeCount(self) -> int:
        return self.nodeCount

    def _negamax(self, position: Position, alpha: int, beta: int, root: bool = False) -> int:
        self.nodeCount += 1
        assert not position.canWinNext()

        next_moves = position.possibleNonLoosingMoves()
        if next_moves == 0:
            return -((Position.WIDTH * Position.HEIGHT - position.nbMoves()) // 2)

        if position.nbMoves() >= Position.WIDTH * Position.HEIGHT - 2:
            if root and next_moves != 0:
                for x in range(Position.WIDTH):
                    col = self.columnOrder[x]
                    if next_moves & position.column_mask(col):
                        self.root_move = col
                        break
            return 0

        minimum = -((Position.WIDTH * Position.HEIGHT - 2 - position.nbMoves()) // 2)
        if alpha < minimum:
            alpha = minimum
            if alpha >= beta:
                return alpha

        max_score = (Position.WIDTH * Position.HEIGHT - 1 - position.nbMoves()) // 2
        if beta > max_score:
            beta = max_score
            if alpha >= beta:
                return beta
            
        val = 0 if root else self.transTable.get(position.key())
        if val != 0:
            threshold = Position.MAX_SCORE - Position.MIN_SCORE + 1
            if val > threshold:
                minimum = val + 2 * Position.MIN_SCORE - Position.MAX_SCORE - 2
                if alpha < minimum:
                    alpha = minimum
                    if alpha >= beta:
                        return alpha
            else:
                max_score = val + Position.MIN_SCORE - 1
                if beta > max_score:
                    beta = max_score
                    if alpha >= beta:
                        return beta

        moves: list[tuple[int, int, int]] = []
        for x in range(Position.WIDTH):
            col = self.columnOrder[x]
            if next_moves & position.column_mask(col):
                move = (position.mask + position.bottom_mask(col)) & position.column_mask(col)
                moves.append((move, position.moveScore(move), col))

        moves.sort(key=lambda item: item[1], reverse=True)

        for move, _, col in moves:
            next_position = position.copy()
            next_position.play(col)
            score = -self._negamax(next_position, -beta, -alpha)

            if score >= beta:
                if root:
                    self.root_move = col
                self.transTable.put(
                    position.key(),
                    score + Position.MAX_SCORE - 2 * Position.MIN_SCORE + 2,
                )
                return score
            if score >= alpha:
                alpha = score
                if root:
                    self.root_move = col

        self.transTable.put(position.key(), alpha - Position.MIN_SCORE + 1)
        return alpha


__all__ = ["Solver"]
