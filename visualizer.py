"""Terminal visualizer for the Connect-4 solver.

Replays a selected game (typed move sequence) with ASCII animation,
then shows the solver's principal variation (best line) with scores.

Usage:
    python visualizer.py 32164625 [--delay 0.8] [--max-plies 42] [--show-all]
    python visualizer.py  # prompts for a move sequence

Move sequence format: digits '1'-'7', one per move, e.g. "444444".
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from position import Position
from solver import Solver

P1 = "X"
P2 = "O"


def decode_stones(position: Position) -> tuple[int, int]:
    """Return (p1_stones, p2_stones) bitboards."""
    current = position.current_position
    opponent = position.mask ^ current
    if position.nbMoves() % 2 == 0:
        # P1 to move: current holds P1 stones.
        return current, opponent
    # P2 to move: current holds P2 stones.
    return opponent, current


def has_won(stones: int) -> bool:
    return Position.alignment(stones)


def game_result(position: Position) -> str | None:
    """Return 'X wins' / 'O wins' / 'Draw' if terminal, else None."""
    p1, p2 = decode_stones(position)
    if has_won(p1):
        return f"{P1} wins"
    if has_won(p2):
        return f"{P2} wins"
    if position.nbMoves() >= Position.WIDTH * Position.HEIGHT:
        return "Draw"
    if not any(position.canPlay(c) for c in range(Position.WIDTH)):
        return "Draw"
    return None


def render_board(position: Position, last_move: int = -1) -> str:
    p1, p2 = decode_stones(position)
    lines = []
    for row in range(Position.HEIGHT - 1, -1, -1):
        cells = []
        for col in range(Position.WIDTH):
            bit = 1 << (col * Position.HEIGHT1 + row)
            if p1 & bit:
                cells.append(P1)
            elif p2 & bit:
                cells.append(P2)
            else:
                cells.append(".")
        lines.append("|" + "|".join(cells) + "|")
    marker = [" "] * Position.WIDTH
    if 0 <= last_move < Position.WIDTH:
        marker[last_move] = "^"
    lines.append(" " + " ".join(marker))
    lines.append(" " + " ".join(str(c + 1) for c in range(Position.WIDTH)))
    return "\n".join(lines)


def interpret_score(score: int) -> str:
    if score > 0:
        return f"winning in {score} moves (side to move)"
    if score < 0:
        return f"losing, opponent wins in {-score} moves"
    return "draw with perfect play"


def clear_screen(enabled: bool) -> None:
    if not enabled:
        return
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def build_position(sequence: str) -> tuple[Position, int]:
    position = Position()
    played = position.play_sequence(sequence)
    return position, played


def solve_with_stats(solver: Solver, position: Position) -> tuple[int, int, int, float]:
    pos = position.copy()
    start = time.perf_counter()
    result = solver.solve(pos, True)
    elapsed = time.perf_counter() - start
    if isinstance(result, tuple):
        score, col = result
    else:  # canWinNext path without return_move never happens here, be safe
        score, col = result, -1
    return score, col, solver.getNodeCount(), elapsed * 1000.0


def all_move_scores(solver: Solver, position: Position) -> list[tuple[int, int]]:
    """Score every legal move as (col, score-from-side-to-move). Sorted best first."""
    scored = []
    for col in range(Position.WIDTH):
        if not position.canPlay(col):
            continue
        if position.isWinningMove(col):
            score = (Position.WIDTH * Position.HEIGHT + 1 - position.nbMoves()) // 2
            scored.append((col, score))
            continue
        child = position.copy()
        child.play(col)
        scored.append((col, -solver.solve(child)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored


def show_frame(
    title: str,
    position: Position,
    last_move: int,
    extra: str = "",
    animate: bool = True,
) -> None:
    clear_screen(animate)
    print(title)
    print(render_board(position, last_move))
    if extra:
        print(extra)
    print()


def replay_game(sequence: str, delay: float, animate: bool) -> Position:
    position = Position()
    played = position.play_sequence(sequence)
    if played != len(sequence):
        print(
            f"Note: only first {played}/{len(sequence)} moves are legal "
            f"(stopped at '{sequence[played:]}'). Replaying legal prefix."
        )
        sequence = sequence[:played]

    replay = Position()
    for i, ch in enumerate(sequence):
        col = ord(ch) - ord("1")
        replay.play(col)
        side = P1 if i % 2 == 0 else P2
        show_frame(
            f"=== Selected game replay: move {i + 1}/{len(sequence)} "
            f"({side} plays {col + 1}) ===",
            replay,
            col,
            animate=animate,
        )
        if animate and delay > 0 and i < len(sequence) - 1:
            time.sleep(delay)
    if not sequence:
        show_frame("=== Empty board (no replay moves) ===", replay, -1, animate=animate)
    return replay


def run_pv(
    start: Position,
    solver: Solver,
    delay: float,
    animate: bool,
    max_plies: int,
    show_all: bool,
) -> list[dict]:
    position = start.copy()
    pv: list[dict] = []
    ply = 0

    while ply < max_plies:
        result = game_result(position)
        if result is not None:
            show_frame(f"=== Game over: {result} ===", position, -1, animate=animate)
            break
        if position.canWinNext():
            score, col, nodes, ms = solve_with_stats(solver, position)
            side = P1 if position.nbMoves() % 2 == 0 else P2
            show_frame(
                f"=== Solving ply {ply + 1}: {side} to move wins immediately ===",
                position,
                -1,
                f"score={score} ({interpret_score(score)}) best={col + 1} "
                f"nodes={nodes} time={ms:.2f}ms",
                animate=animate,
            )
            pv.append({"move": col, "score": score, "nodes": nodes, "ms": ms})
            position.play(col)
            ply += 1
            if animate and delay > 0:
                time.sleep(delay)
            continue

        next_moves = position.possibleNonLoosingMoves()
        if next_moves == 0:
            show_frame(
                "=== Solving stopped: no non-losing moves (forced loss) ===",
                position,
                -1,
                animate=animate,
            )
            break

        score, col, nodes, ms = solve_with_stats(solver, position)
        side = P1 if position.nbMoves() % 2 == 0 else P2
        extra = (
            f"position moves={position.nbMoves()} score={score} "
            f"({interpret_score(score)})\nbest move: {side} plays {col + 1} "
            f"nodes={nodes} time={ms:.2f}ms"
        )
        if show_all:
            ranked = all_move_scores(solver, position)
            table = "all moves: " + " ".join(f"{c + 1}:{s:+d}" for c, s in ranked)
            extra += "\n" + table
        pv.append({"move": col, "score": score, "nodes": nodes, "ms": ms})
        show_frame(f"=== Solving ply {ply + 1}: {side} to move ===", position, -1, extra, animate)
        if animate and delay > 0:
            time.sleep(delay)

        position.play(col)
        show_frame(
            f"=== Principal variation: ply {ply + 1} played ({side} -> {col + 1}) ===",
            position,
            col,
            animate=animate,
        )
        if animate and delay > 0:
            time.sleep(delay)
        ply += 1
    else:
        print(f"Stopped after max-plies={max_plies}.")
    return pv


def print_summary(pv: list[dict]) -> None:
    if not pv:
        print("No solving steps (game was already over).")
        return
    print("Principal variation summary:")
    print(f"{'ply':>4} {'move':>5} {'score':>7} {'nodes':>10} {'time_ms':>9}")
    for i, step in enumerate(pv, start=1):
        print(
            f"{i:>4} {step['move'] + 1:>5} {step['score']:>+7d} "
            f"{step['nodes']:>10d} {step['ms']:>9.2f}"
        )
    line = "".join(str(s["move"] + 1) for s in pv)
    print(f"PV move line (1-based cols): {line}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize the Connect-4 solving process.")
    parser.add_argument("sequence", nargs="?", default=None, help="Move sequence, e.g. 32164625")
    parser.add_argument("--delay", type=float, default=0.8, help="Seconds between frames")
    parser.add_argument("--no-animate", action="store_true", help="Print frames without clearing")
    parser.add_argument("--max-plies", type=int, default=42, help="Max PV plies to solve")
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Score all legal moves at each PV node (slower)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    sequence = args.sequence
    if sequence is None:
        try:
            sequence = input("Enter move sequence (digits 1-7, e.g. 32164625): ").strip()
        except EOFError:
            sequence = ""
    sequence = (sequence or "").strip()

    animate = not args.no_animate
    solver = Solver()

    print(f"Selected game: '{sequence}'")
    start = replay_game(sequence, args.delay, animate)

    result = game_result(start)
    if result is not None:
        print(f"Game already over after replay: {result}")
        return

    print("--- Solving from replayed position ---")
    if start.nbMoves() < 8:
        print(
            "Warning: early position with "
            f"{start.nbMoves()} moves may take very long to solve. "
            "Consider a longer sequence or Ctrl-C to abort."
        )
    pv = run_pv(start, solver, args.delay, animate, args.max_plies, args.show_all)
    print_summary(pv)


if __name__ == "__main__":
    main()
