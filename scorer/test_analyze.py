#!/usr/bin/env python3
"""Unit tests for scorer/analyze.py."""

import csv
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import (
    bootstrap_diff,
    detect,
    main,
    run_analysis,
    sign_test_p,
    to_bool,
)


def test_to_bool():
    for v in ["1", "true", "True", "t", "yes", "pass", "passed", "PASS"]:
        assert to_bool(v) is True, f"Expected {v!r} to be True"
    for v in ["0", "false", "False", "f", "no", "fail", "failed", ""]:
        assert to_bool(v) is False, f"Expected {v!r} to be False"

    try:
        to_bool("maybe")
        assert False, "Expected ValueError for invalid boolean string"
    except ValueError:
        pass


def test_sign_test_p():
    assert sign_test_p(0, 0) == 1.0
    assert sign_test_p(5, 5) == 1.0
    p10_0 = sign_test_p(10, 0)
    p0_10 = sign_test_p(0, 10)
    assert p10_0 == p0_10
    assert abs(p10_0 - (2 / 1024)) < 1e-6
    assert sign_test_p(1, 0) == 1.0


def test_bootstrap_diff():
    lo, hi = bootstrap_diff([1.0, 1.0, 1.0], [0.0, 0.0, 0.0], reps=500, seed=42)
    assert lo == 100.0 and hi == 100.0

    lo, hi = bootstrap_diff([0.0, 0.0], [1.0, 1.0], reps=500, seed=42)
    assert lo == -100.0 and hi == -100.0

    lo, hi = bootstrap_diff([1.0, 0.0], [1.0, 0.0], reps=500, seed=42)
    assert lo <= 0.0 <= hi


def test_detect():
    headers = ["Run_ID", "Database", "System", "Question_ID", "Passed"]
    assert detect(headers, "db", None) == "Database"
    assert detect(headers, "system", None) == "System"
    assert detect(headers, "question", None) == "Question_ID"
    assert detect(headers, "run", None) == "Run_ID"
    assert detect(headers, "passed", None) == "Passed"
    assert detect(headers, "db", "Custom_DB") == "Custom_DB"


def test_run_analysis_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mock_results.csv")
        md_out = os.path.join(tmpdir, "report.md")
        matrix_out = os.path.join(tmpdir, "matrix.csv")

        # Create a mock CSV with 2 questions, 2 runs, 2 systems:
        # q1: baseline fails (0/2), tool_a passes (2/2) -> fixed=1, broke=0
        # q2: baseline passes (2/2), tool_a passes (1/2 split)
        # q_ambig: category ambiguous -> should be excluded
        # q_infra: infra_error = true -> should be dropped
        rows = [
            {"db": "demo", "system": "baseline", "question": "q1", "run": "1", "passed": "0", "category": "clean", "infra_error": "0"},
            {"db": "demo", "system": "baseline", "question": "q1", "run": "2", "passed": "0", "category": "clean", "infra_error": "0"},
            {"db": "demo", "system": "tool_a", "question": "q1", "run": "1", "passed": "1", "category": "clean", "infra_error": "0"},
            {"db": "demo", "system": "tool_a", "question": "q1", "run": "2", "passed": "1", "category": "clean", "infra_error": "0"},
            {"db": "demo", "system": "baseline", "question": "q2", "run": "1", "passed": "1", "category": "clean", "infra_error": "0"},
            {"db": "demo", "system": "baseline", "question": "q2", "run": "2", "passed": "1", "category": "clean", "infra_error": "0"},
            {"db": "demo", "system": "tool_a", "question": "q2", "run": "1", "passed": "1", "category": "clean", "infra_error": "0"},
            {"db": "demo", "system": "tool_a", "question": "q2", "run": "2", "passed": "0", "category": "clean", "infra_error": "0"},
            # Ambiguous question (should be ignored)
            {"db": "demo", "system": "baseline", "question": "q_ambig", "run": "1", "passed": "0", "category": "ambiguous", "infra_error": "0"},
            {"db": "demo", "system": "tool_a", "question": "q_ambig", "run": "1", "passed": "1", "category": "ambiguous", "infra_error": "0"},
            # Infra error row (should be dropped)
            {"db": "demo", "system": "baseline", "question": "q1", "run": "3", "passed": "0", "category": "clean", "infra_error": "1"},
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        # 1. Test run_analysis with default majority (ties="fail")
        buf = io.StringIO()
        with redirect_stdout(buf):
            text, matrix_dict = run_analysis(
                csv_path=csv_path,
                baseline="baseline",
                out=md_out,
                matrix=matrix_out,
                ties="fail",
                quiet=False,
            )

        assert os.path.exists(md_out), "Expected markdown report file to be written"
        assert os.path.exists(matrix_out), "Expected per-question matrix CSV to be written"
        assert "Rows dropped for infrastructure errors: 1" in text
        assert "## demo  (2 questions)" in text
        assert "| baseline | 1/2 | 50.0% |" in text
        assert "| tool_a | 1/2 | 50.0% | 1 |" in text  # q2 was split (1/2), so flaky=1
        assert "Wrote markdown report to" in buf.getvalue()

        # Check matrix contents
        with open(matrix_out, encoding="utf-8") as f:
            matrix_rows = list(csv.DictReader(f))
        assert len(matrix_rows) == 2
        q1_row = next(r for r in matrix_rows if r["question"] == "q1")
        assert q1_row["baseline"] == "0/2"
        assert q1_row["tool_a"] == "2/2"

        # 2. Test CLI with --markdown-out and --quiet
        md_cli_out = os.path.join(tmpdir, "cli_report.md")
        matrix_cli_out = os.path.join(tmpdir, "cli_matrix.csv")
        buf_quiet = io.StringIO()
        with redirect_stdout(buf_quiet):
            main([csv_path, "--markdown-out", md_cli_out, "--matrix", matrix_cli_out, "--quiet", "--ties", "half"])

        assert os.path.exists(md_cli_out), "Expected CLI --markdown-out report file"
        assert buf_quiet.getvalue() == "", "Expected --quiet to suppress stdout"
        cli_text = open(md_cli_out, encoding="utf-8").read()
        # Under ties="half", q2 for tool_a is 0.5, total tool_a score is 1.5/2 = 75.0%
        assert "| tool_a | 1.5/2 | 75.0% |" in cli_text

        # 3. Test CLI backward compatibility with --out
        md_legacy_out = os.path.join(tmpdir, "legacy_report.md")
        matrix_legacy_out = os.path.join(tmpdir, "legacy_matrix.csv")
        main([csv_path, "--out", md_legacy_out, "--matrix", matrix_legacy_out, "-q"])
        assert os.path.exists(md_legacy_out)


def run_all_tests():
    test_to_bool()
    test_sign_test_p()
    test_bootstrap_diff()
    test_detect()
    test_run_analysis_end_to_end()
    print("analyze.py: all unit and integration tests passed")


if __name__ == "__main__":
    run_all_tests()
