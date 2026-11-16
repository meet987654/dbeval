#!/usr/bin/env python3
"""Unit tests for scorer/conversation.py (multi-turn question support)."""

import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from conversation import contextualize, conversation_results, expand, turn_id


def test_contextualize():
    assert contextualize("How many?", None) == "How many?"
    assert contextualize("How many?", []) == "How many?"
    text = contextualize("Break them down by country.", [
        ("How many accounts do we have?", "SELECT COUNT(*) FROM accounts"),
        ("How many are on scale?", None),
    ])
    assert "Turn 1 question: How many accounts do we have?" in text
    assert "Turn 1 SQL: SELECT COUNT(*) FROM accounts" in text
    assert "Turn 2 SQL: (no SQL was produced)" in text
    assert text.rstrip().endswith("Break them down by country.")


def test_expand():
    single = {"id": "x-1", "question": "Q?", "gold_sql": "SELECT 1", "category": "simple"}
    conv = {"id": "c-1", "category": "conversation", "turns": [
        {"question": "A?", "gold_sql": "SELECT 1"},
        {"question": "B?", "gold_sql": "SELECT 2", "ordered": True},
    ]}
    out = expand([single, conv])
    assert out[0]["id"] == "x-1" and out[0]["conv_id"] is None and out[0]["turn"] is None
    assert [t["id"] for t in out[1:]] == [turn_id("c-1", 1), turn_id("c-1", 2)] == ["c-1#t1", "c-1#t2"]
    assert [t["conv_id"] for t in out[1:]] == ["c-1", "c-1"]
    assert [t["turn"] for t in out[1:]] == [1, 2]
    assert out[1]["ordered"] is False and out[2]["ordered"] is True
    assert out[1]["category"] == "conversation"


def test_conversation_results():
    recs = [
        {"system": "s", "db": "d", "run_num": 1, "question_id": "c-1#t2", "passed": False},
        {"system": "s", "db": "d", "run_num": 1, "question_id": "c-1#t1", "passed": True},
        {"system": "s", "db": "d", "run_num": 1, "question_id": "plain-1", "passed": True},
        {"system": "s", "db": "d", "run_num": 2, "question_id": "c-1#t1", "passed": True},
        {"system": "s", "db": "d", "run_num": 2, "question_id": "c-1#t2", "passed": True},
    ]
    res = conversation_results(recs)
    assert res == {("s", "d", 1, "c-1"): [True, False], ("s", "d", 2, "c-1"): [True, True]}


def test_shipped_conversation_suite_expands():
    with open(os.path.join(ROOT, "questions", "appdb_conversations.yaml"), encoding="utf-8") as f:
        entries = yaml.safe_load(f)
    turns = expand(entries)
    assert len(entries) >= 3 and len(turns) > len(entries)
    assert all(t["gold_sql"] and t["question"] and t["conv_id"] for t in turns)


def run_all_tests():
    test_contextualize()
    test_expand()
    test_conversation_results()
    test_shipped_conversation_suite_expands()
    print("conversation.py: all unit tests passed")


if __name__ == "__main__":
    run_all_tests()
