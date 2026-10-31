#!/usr/bin/env python3
"""Unit tests for scorer/validate_questions.py."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_questions import validate_question


def run_tests():
    global_ids = set()

    # 1. Valid question passes
    q_valid = {
        "id": "test-001",
        "question": "How many rows are in the database?",
        "gold_sql": "SELECT COUNT(*) FROM table_a",
        "category": "simple",
    }
    errs = validate_question(q_valid, 1, "test.yaml", global_ids)
    assert not errs, f"Expected no errors, got: {errs}"
    assert "test-001" in global_ids

    # 2. Duplicate ID fails
    errs = validate_question(q_valid, 2, "test.yaml", global_ids)
    assert any("duplicate" in e.lower() for e in errs), f"Expected duplicate error, got: {errs}"

    # 3. Missing ID fails
    q_no_id = {
        "question": "Valid question?",
        "gold_sql": "SELECT 1",
    }
    errs = validate_question(q_no_id, 3, "test.yaml", global_ids)
    assert any("missing or invalid 'id'" in e.lower() for e in errs), f"Expected missing id error, got: {errs}"

    # 4. Missing gold_sql on non-ambiguous question fails
    q_no_sql = {
        "id": "test-002",
        "question": "What is total revenue?",
        "category": "metric",
    }
    errs = validate_question(q_no_sql, 4, "test.yaml", global_ids)
    assert any("missing or empty 'gold_sql'" in e.lower() for e in errs), f"Expected missing sql error, got: {errs}"

    # 5. Invalid SQL prefix fails
    q_bad_sql = {
        "id": "test-003",
        "question": "Update revenue?",
        "gold_sql": "DROP TABLE accounts",
    }
    errs = validate_question(q_bad_sql, 5, "test.yaml", global_ids)
    assert any("must start with one of" in e.lower() for e in errs), f"Expected prefix error, got: {errs}"

    # 6. Ambiguous question with expected explanation passes
    q_ambig = {
        "id": "test-004",
        "question": "Who is best?",
        "category": "ambiguous",
        "gold_sql": None,
        "expected": "Clarify metric of best (tenure or revenue).",
    }
    errs = validate_question(q_ambig, 6, "test.yaml", global_ids)
    assert not errs, f"Expected ambiguous question to pass, got: {errs}"

    # 7. Ambiguous question without expected explanation fails
    q_ambig_no_exp = {
        "id": "test-005",
        "question": "Who is best?",
        "category": "ambiguous",
        "gold_sql": None,
    }
    errs = validate_question(q_ambig_no_exp, 7, "test.yaml", global_ids)
    assert any("expected" in e.lower() for e in errs), f"Expected missing expected error, got: {errs}"

    # 8. Non-boolean ordered fails
    q_bad_ordered = {
        "id": "test-006",
        "question": "Sorted accounts?",
        "gold_sql": "SELECT id FROM accounts ORDER BY id",
        "ordered": "yes",
    }
    errs = validate_question(q_bad_ordered, 8, "test.yaml", global_ids)
    assert any("ordered" in e.lower() for e in errs), f"Expected ordered error, got: {errs}"

    print("validate_questions.py: all unit tests passed")


if __name__ == "__main__":
    run_tests()
