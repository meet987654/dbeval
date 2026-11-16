#!/usr/bin/env python3
"""Unit tests for scorer/report_html.py."""

import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_html import load_results


def test_load_results():
    rows = [
        ["demo", "baseline", "q1", "1", "1", "clean", "0"],
        ["demo", "baseline", "q1", "2", "0", "clean", "0"],
        ["demo", "baseline", "q2", "1", "1", "clean", "0"],
        ["demo", "tool_a", "q1", "1", "1", "clean", "0"],
        ["demo", "tool_a", "q1", "2", "1", "clean", "0"],
        ["demo", "tool_a", "q2", "1", "0", "clean", "0"],
        ["demo", "baseline", "q3", "1", "0", "ambiguous", "0"],
        ["demo", "tool_a", "q3", "1", "1", "clean", "1"],
    ]

    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "results.csv")

        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "db", "system", "question_id", "run_num",
                "passed", "category", "infra_error",
            ])
            writer.writerows(rows)

        result = load_results(path)

    assert result["total_rows"] == 8
    assert result["included_rows"] == 6
    assert result["dropped_ambiguous"] == 1
    assert result["dropped_infra"] == 1

    baseline_q1 = result["databases"]["demo"]["baseline"]["q1"]
    assert baseline_q1["runs"] == [True, False]
    assert baseline_q1["passed"] == 1
    assert baseline_q1["total_runs"] == 2
    assert baseline_q1["flaky"] is True

    tool_q1 = result["databases"]["demo"]["tool_a"]["q1"]
    assert tool_q1["runs"] == [True, True]
    assert tool_q1["flaky"] is False

    assert "q3" not in result["databases"]["demo"]["baseline"]
    assert "q3" not in result["databases"]["demo"]["tool_a"]


def test_missing_file():
    try:
        load_results("/tmp/dbeval-file-that-does-not-exist.csv")
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError:
        pass


def test_empty_file():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "empty.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("db,system,question_id,run_num,passed\n")

        try:
            load_results(path)
            raise AssertionError("Expected ValueError")
        except ValueError as error:
            assert "empty" in str(error).lower()


def run_all_tests():
    test_load_results()
    test_missing_file()
    test_empty_file()
    print("report_html.py: all data-processing tests passed")


if __name__ == "__main__":
    run_all_tests()
