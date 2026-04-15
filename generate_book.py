"""Opening-book generator for the Connect4 solver.

This script builds a precomputed opening book for early positions and saves it
as a pickle file.
"""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

from position import Position
from solver import Solver

from tqdm import tqdm


def build_opening_book(
    solver: Solver,
    max_moves: int = 8,
    use_tqdm: bool = True,
) -> dict[int, tuple[int, int]]:
    opening_book: dict[int, tuple[int, int]] = {}
    progress = None
    if use_tqdm and tqdm is not None:
        progress = tqdm(desc="Generating opening book", unit="pos")
    _build_opening_book(solver, Position(), max_moves, opening_book, progress)
    if progress is not None:
        progress.close()
    return opening_book


def _build_opening_book(
    solver: Solver,
    position: Position,
    max_moves: int,
    opening_book: dict[int, tuple[int, int]],
    progress,
) -> None:
    if progress is not None:
        progress.update(1)

    if position.nbMoves() >= max_moves:
        return
    if position.canWinNext():
        return

    next_moves = position.possibleNonLoosingMoves()
    if next_moves == 0:
        return

    best_score = None
    best_col = None

    for x in range(Position.WIDTH):
        col = solver.columnOrder[x]
        if next_moves & position.column_mask(col):
            candidate = position.copy()
            candidate.play(col)
            score = -solver.solve(candidate)
            if best_score is None or score > best_score:
                best_score = score
                best_col = col

    if best_col is None:
        return

    opening_book[position.key()] = (best_col, best_score)

    for x in range(Position.WIDTH):
        col = solver.columnOrder[x]
        if next_moves & position.column_mask(col):
            child = position.copy()
            child.play(col)
            _build_opening_book(solver, child, max_moves, opening_book, progress)

    if progress is not None:
        progress.update(1)


def save_opening_book(opening_book: dict[int, tuple[int, int]], filename: Path) -> None:
    with filename.open("wb") as handle:
        pickle.dump(opening_book, handle)


def load_opening_book(filename: Path) -> dict[int, tuple[int, int]]:
    with filename.open("rb") as handle:
        return pickle.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Connect4 opening book.")
    parser.add_argument("--max-moves", type=int, default=8, help="Maximum number of moves to precompute")
    parser.add_argument("--output", type=Path, default=Path("opening_book.pkl"), help="Output pickle file")
    args = parser.parse_args()

    solver = Solver()
    opening_book = build_opening_book(solver, args.max_moves)
    save_opening_book(opening_book, args.output)
    print(f"Saved opening book with {len(opening_book)} entries to {args.output}")


if __name__ == "__main__":
    main()
