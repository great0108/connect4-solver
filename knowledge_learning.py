"""Knowledge-based rule learning for Connect4.

This module provides a Python implementation of a simple rule learner
that builds and evolves a knowledge-based move selector from Position data.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from position import Position
from solver import Solver

RuleToken = str
RULE_TOKENS: list[RuleToken] = ["@", "|", " ", "+", "=", "-", "!"]

DEFAULT_PRIORITY: list[RuleToken] = ["!", "@", "claim", "+", "=", "-"]


def progress(
    iterable,
    desc: str | None = None,
    total: int | None = None,
    unit: str | None = None,
    use_tqdm: bool = True,
):
    if use_tqdm and tqdm is not None:
        return tqdm(iterable, desc=desc, total=total, unit=unit)
    return iterable


def legal_columns(position: Position) -> list[int]:
    return [col for col in range(Position.WIDTH) if position.canPlay(col)]


def play_row(position: Position, col: int) -> int | None:
    if not position.canPlay(col):
        return None
    col_base = col * Position.HEIGHT1
    for y in range(Position.HEIGHT):
        if not (position.mask >> (col_base + y)) & 1:
            return y
    return None


def is_winning_move(position: Position, col: int) -> bool:
    return position.isWinningMove(col)


def blocking_moves(position: Position) -> list[int]:
    if position.canWinNext():
        return []

    opponent_threats: list[int] = []
    for col in legal_columns(position):
        probe = position.copy()
        probe.play(col)
        if probe.canWinNext():
            opponent_threats.append(col)
    return opponent_threats


@dataclass
class KnowledgeRule:
    grid: list[list[RuleToken]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.grid:
            self.grid = self.random_grid()
        self._normalize_grid()

    def _normalize_grid(self) -> None:
        if len(self.grid) != Position.HEIGHT or any(len(row) != Position.WIDTH for row in self.grid):
            raise ValueError("KnowledgeRule grid must be 6 rows by 7 columns")

    @staticmethod
    def random_grid() -> list[list[RuleToken]]:
        return [[random.choice(RULE_TOKENS) for _ in range(Position.WIDTH)] for _ in range(Position.HEIGHT)]

    def copy(self) -> KnowledgeRule:
        return KnowledgeRule([row.copy() for row in self.grid])

    def mutate(self, change_rate: float = 0.08) -> None:
        total_cells = Position.WIDTH * Position.HEIGHT
        mutations = max(1, int(total_cells * change_rate))
        for _ in range(mutations):
            x = random.randrange(Position.WIDTH)
            y = random.randrange(Position.HEIGHT)
            self.grid[y][x] = random.choice(RULE_TOKENS)

    def serialize(self) -> str:
        return json.dumps(self.grid)

    @classmethod
    def deserialize(cls, text: str) -> KnowledgeRule:
        data = json.loads(text)
        return KnowledgeRule(data)

    def _row_parity_matches(self, row: int, token: RuleToken) -> bool:
        if token == "|":
            return row % 2 == 1
        if token == " ":
            return row % 2 == 0
        return False

    def query_move(self, position: Position) -> int:
        wins = [col for col in legal_columns(position) if is_winning_move(position, col)]
        if wins:
            return wins[0]

        blocks = blocking_moves(position)
        if blocks:
            return blocks[0]

        legal_cols = legal_columns(position)
        if not legal_cols:
            raise ValueError("No legal moves available")

        column_targets: dict[int, RuleToken] = {}
        for col in legal_cols:
            row = play_row(position, col)
            if row is None:
                continue
            column_targets[col] = self.grid[row][col]

        for token in DEFAULT_PRIORITY:
            candidates: list[int] = []
            for col, token_at_drop in column_targets.items():
                if token == "claim":
                    if self._row_parity_matches(play_row(position, col), token_at_drop):
                        candidates.append(col)
                elif token_at_drop == token:
                    candidates.append(col)

            if len(candidates) == 1:
                return candidates[0]
            if candidates:
                return self._choose_best_candidate(candidates)

        return self._choose_best_candidate(legal_cols)

    @staticmethod
    def _choose_best_candidate(candidates: list[int]) -> int:
        center = Position.WIDTH // 2
        return min(candidates, key=lambda col: abs(col - center))

    def as_text(self) -> str:
        return "\n".join("".join(row) for row in reversed(self.grid))


@dataclass
class KnowledgeExample:
    position: Position
    best_move: int


def generate_random_positions(num_positions: int, max_moves: int = 8, use_tqdm: bool = True) -> list[Position]:
    positions: list[Position] = []
    for _ in progress(range(num_positions), desc="Generating positions", unit="pos", use_tqdm=use_tqdm):
        position = Position()
        moves = random.randrange(max_moves + 1)
        for _ in range(moves):
            legal = legal_columns(position)
            if not legal:
                break
            position.play(random.choice(legal))
            if position.canWinNext():
                break
        positions.append(position)
    return positions


def build_training_examples(
    solver: Solver,
    positions: Iterable[Position],
    use_tqdm: bool = True,
) -> list[KnowledgeExample]:
    examples: list[KnowledgeExample] = []
    position_list = list(positions)
    for position in progress(position_list, desc="Building training examples", unit="pos", use_tqdm=use_tqdm):
        if position.canWinNext():
            continue
        next_moves = position.possibleNonLoosingMoves()
        if next_moves == 0:
            continue

        best_col = None
        best_score = None

        for x in range(Position.WIDTH):
            if next_moves & position.column_mask(x):
                child = position.copy()
                child.play(x)
                score = -solver.solve(child)
                if best_score is None or score > best_score:
                    best_score = score
                    best_col = x

        if best_col is not None:
            examples.append(KnowledgeExample(position.copy(), best_col))
    return examples


def evaluate_rule(rule: KnowledgeRule, examples: Iterable[KnowledgeExample]) -> int:
    correct = 0
    for example in examples:
        try:
            predicted = rule.query_move(example.position)
        except ValueError:
            continue
        if predicted == example.best_move:
            correct += 1
    return correct


@dataclass
class KnowledgeLearner:
    solver: Solver
    examples: list[KnowledgeExample]
    population_size: int = 10
    generations: int = 100
    mutation_rate: float = 0.08

    def train(self, use_tqdm: bool = True) -> KnowledgeRule:
        population = [KnowledgeRule() for _ in range(self.population_size)]
        scores = [evaluate_rule(rule, self.examples) for rule in population]
        best_index = max(range(len(population)), key=lambda i: scores[i])
        best_rule = population[best_index].copy()
        best_score = scores[best_index]

        iterations = progress(
            range(self.generations),
            desc="Training knowledge rule",
            unit="gen",
            use_tqdm=use_tqdm,
        )
        for _ in iterations:
            candidate = best_rule.copy()
            candidate.mutate(self.mutation_rate)
            score = evaluate_rule(candidate, self.examples)
            if score >= best_score:
                best_rule = candidate
                best_score = score
        return best_rule

    def save_rule(self, filepath: Path, rule: KnowledgeRule) -> None:
        filepath.write_text(rule.serialize(), encoding="utf-8")

    def load_rule(self, filepath: Path) -> KnowledgeRule:
        return KnowledgeRule.deserialize(filepath.read_text(encoding="utf-8"))


def example_training_pipeline(
    num_examples: int = 20,
    max_moves: int = 14,
    population_size: int = 15,
    generations: int = 50,
    use_tqdm: bool = True,
) -> KnowledgeRule:
    solver = Solver()
    positions = generate_random_positions(num_examples, max_moves=max_moves, use_tqdm=use_tqdm)
    examples = build_training_examples(solver, positions, use_tqdm=use_tqdm)
    learner = KnowledgeLearner(
        solver=solver,
        examples=examples,
        population_size=population_size,
        generations=generations,
    )
    return learner.train(use_tqdm=use_tqdm)


if __name__ == "__main__":
    trained_rule = example_training_pipeline()
    print("Trained knowledge rule:")
    print(trained_rule.as_text())
