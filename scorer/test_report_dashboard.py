#!/usr/bin/env python3
"""Integration tests for standalone HTML dashboard generation."""

import csv
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_html import build_dashboard_data, render_dashboard


def create_csv(path):
    rows = [
        ["demo", "baseline", "q1", "1", "1", "clean", "0"],
        ["demo", "baseline", "q1", "2", "1", "clean", "0"],
        ["demo", "baseline", "q2", "1", "0", "clean", "0"],
        ["demo", "baseline", "q2", "2", "1", "clean", "0"],
        ["demo", "tool_a", "q1", "1", "1", "clean", "0"],
        ["demo", "tool_a", "q1", "2", "1", "clean", "0"],
        ["demo", "tool_a", "q2", "1", "1", "clean", "0"],
        ["demo", "tool_a", "q2", "2", "1", "clean", "0"],
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "db", "system", "question_id", "run_num",
            "passed", "category", "infra_error",
        ])
        writer.writerows(rows)


def test_dashboard_data():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "sample.csv"
        create_csv(source)

        datasets = build_dashboard_data(
            [source], reps=500, seed=42
        )

    assert len(datasets) == 1

    dataset = datasets[0]
    assert dataset["source"] == "sample.csv"

    db = dataset["databases"]["demo"]
    assert db["question_ids"] == ["q1", "q2"]

    baseline = db["systems"]["baseline"]["summary"]
    assert baseline["answered_questions"] == 2
    assert baseline["accuracy"] == 50.0
    assert baseline["flaky_questions"] == 1

    tool = db["systems"]["tool_a"]["summary"]
    assert tool["accuracy"] == 100.0

    assert db["systems"]["baseline"]["questions"]["q2"]["status"] == "flaky"


def test_render_dashboard():
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "sample.csv"
        output = Path(directory) / "dashboard.html"
        create_csv(source)

        result = render_dashboard(
            [source], output, reps=500, seed=42
        )

        assert result == output
        assert output.is_file()

        html = output.read_text(encoding="utf-8")
        assert "dbeval Benchmark Dashboard" in html
        assert "System Accuracy Comparison" in html
        assert "Flakiness Breakdown" in html
        assert "Question-Level Pass/Fail Heatmap" in html
        assert "Switch to dark mode" in html
        assert "sample.csv" in html
        assert "https://" not in html
        assert "http://" not in html


def run_all_tests():
    test_dashboard_data()
    test_render_dashboard()
    print("report_html.py: all dashboard integration tests passed")


if __name__ == "__main__":
    run_all_tests()
