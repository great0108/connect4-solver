"""Run solver checks against test data files.

Reads each file in the "test data" folder and checks that the solver
returns the expected score for each position string.
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import time

from position import Position
from solver import Solver

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

DATA_DIR = Path(__file__).resolve().parent / "test data"


def parse_test_line(line: str) -> tuple[str, int] | None:
    tokens = line.strip().split()
    if len(tokens) < 2:
        return None
    sequence = tokens[0]
    try:
        expected_score = int(tokens[1])
    except ValueError:
        return None
    return sequence, expected_score


def load_tests(data_dir: Path, file_name: str | None = None) -> list[tuple[Path, int, str, int]]:
    tests = []
    paths = sorted(data_dir.glob("*.txt"))
    if file_name is not None:
        requested = Path(file_name)
        if requested.is_absolute() or requested.parent != Path(""):
            if requested.exists() and requested.suffix == ".txt":
                paths = [requested]
            else:
                raise FileNotFoundError(f"Test file not found: {file_name}")
        else:
            base_name = requested.name
            matches = [p for p in paths if p.name == base_name]
            if not matches:
                raise FileNotFoundError(f"Test file not found in '{data_dir}': {file_name}")
            paths = matches

    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                parsed = parse_test_line(line)
                if parsed is None:
                    continue
                sequence, expected_score = parsed
                tests.append((path, line_number, sequence, expected_score))
    return tests


def build_position(sequence: str) -> Position:
    position = Position()
    played = position.play_sequence(sequence)
    if played != len(sequence):
        raise ValueError(f"Invalid sequence '{sequence}' after {played} moves")
    return position


def run_tests(selected_file: str | None = None) -> None:
    solver = Solver()
    tests = load_tests(DATA_DIR, selected_file)
    total = len(tests)
    passed = 0
    failed = 0
    total_time_ms = 0.0
    failures: list[tuple[str, int, int, int]] = []

    summary_source = selected_file or str(DATA_DIR)
    print(f"Testing {total} positions from '{summary_source}'\n")

    iterator = tqdm(tests, total=total, unit="pos", desc="Progress") if tqdm else tests
    for file_path, line_number, sequence, expected_score in iterator:
        try:
            position = build_position(sequence)
        except ValueError as exc:
            print(f"[ERROR] {file_path.name}:{line_number}: invalid sequence: {exc}")
            failed += 1
            continue

        start_ns = time.perf_counter_ns()
        actual_score = solver.solve(position)
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        total_time_ms += elapsed_ms

        if actual_score == expected_score:
            passed += 1
        else:
            failed += 1
            failures.append((file_path.name, line_number, expected_score, actual_score))

    if tqdm and hasattr(iterator, "close"):
        iterator.close()

    print("\nSummary:")
    print(f"  total positions: {total}")
    print(f"  passed: {passed}")
    print(f"  failed: {failed}")
    print(f"  total solve time: {total_time_ms:.3f}ms")
    if total > 0:
        print(f"  average solve time: {total_time_ms/total:.3f}ms")

    if failures:
        print("\nFailed positions:")
        for file_name, line_number, expected_score, actual_score in failures:
            print(
                f"  {file_name}:{line_number} expected={expected_score} actual={actual_score}"
            )


def parse_args() -> str | None:
    parser = ArgumentParser(description="Run solver tests using test data files.")
    parser.add_argument(
        "file",
        nargs="?",
        help="Optional test data filename under the 'test data' folder to run. If omitted, all files are used.",
    )
    args = parser.parse_args()
    return args.file


if __name__ == "__main__":
    # run_tests(parse_args())
    run_tests("Test_L3_R1.txt")