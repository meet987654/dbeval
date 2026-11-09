#!/usr/bin/env python3
"""Tests for dashboard statistical calculations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_html import (
    bootstrap_accuracy,
    majority_score,
    question_status,
    summarize_system,
)


def test_majority_score():
    assert majority_score([True, True, False]) == 1
    assert majority_score([True, False]) == 0
    assert majority_score([False, False, True]) == 0
    assert majority_score([True]) == 1
    assert majority_score([]) is None


def test_bootstrap_accuracy():
    scores = [1, 1, 0, 1, 0]

    first = bootstrap_accuracy(scores, reps=1000, seed=42)
    second = bootstrap_accuracy(scores, reps=1000, seed=42)

    assert first == second
    assert 0 <= first[0] <= first[1] <= 100

    assert bootstrap_accuracy([], reps=1000) == (None, None)


def test_system_summary():
    questions = {
        "q1": {
            "runs": [True, True, True],
            "passed": 3,
            "total_runs": 3,
            "flaky": False,
        },
        "q2": {
            "runs": [True, False, True],
            "passed": 2,
            "total_runs": 3,
            "flaky": True,
        },
        "q3": {
            "runs": [False, False, False],
            "passed": 0,
            "total_runs": 3,
            "flaky": False,
        },
    }

    result = summarize_system(
        questions,
        ["q1", "q2", "q3", "q4"],
        reps=1000,
        seed=42,
    )

    assert result["answered_questions"] == 3
    assert result["total_questions"] == 4
    assert result["coverage"] == 75.0
    assert result["accuracy"] == (2 / 3) * 100
    assert result["flaky_questions"] == 1
    assert result["assessable_questions"] == 3
    assert abs(result["flakiness_rate"] - (1 / 3) * 100) < 1e-9
    assert result["ci_low"] <= result["accuracy"] <= result["ci_high"]


def test_missing_and_heatmap_status():
    questions = {
        "q1": {
            "runs": [True, True],
            "passed": 2,
            "total_runs": 2,
            "flaky": False,
        },
        "q2": {
            "runs": [True, False],
            "passed": 1,
            "total_runs": 2,
            "flaky": True,
        },
        "q3": {
            "runs": [False, False],
            "passed": 0,
            "total_runs": 2,
            "flaky": False,
        },
    }

    assert question_status(questions, "q1") == "pass"
    assert question_status(questions, "q2") == "flaky"
    assert question_status(questions, "q3") == "fail"
    assert question_status(questions, "q4") == "missing"


def run_all_tests():
    test_majority_score()
    test_bootstrap_accuracy()
    test_system_summary()
    test_missing_and_heatmap_status()
    print("report_html.py: all statistical tests passed")


if __name__ == "__main__":
    run_all_tests()
