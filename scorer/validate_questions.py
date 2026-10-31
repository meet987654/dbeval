#!/usr/bin/env python3
"""Validate question suites in questions/*.yaml:
1. Verifies YAML syntax and structure (must be a list of question dicts).
2. Verifies required keys: 'id', 'question', and 'gold_sql' (or 'expected' for ambiguous questions).
3. Verifies that all question IDs are non-empty strings and strictly unique across suites.
4. Verifies that gold_sql for scored questions starts with a read-only query statement (SELECT / WITH).
5. Verifies that ambiguous questions (category: ambiguous) define an 'expected' clarification guide.
6. Verifies optional typing (e.g. 'ordered' must be a boolean if present).

Usage:
    python scorer/validate_questions.py
    python scorer/validate_questions.py questions/appdb.yaml questions/olist.yaml
"""

import argparse
import os
import re
import sys
from typing import Dict, List, Set, Tuple

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DEFAULT_FILES = [
    os.path.join(ROOT, "questions", "appdb.yaml"),
    os.path.join(ROOT, "questions", "olist.yaml"),
]

ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
VALID_SQL_PREFIXES = ("select", "with")


def validate_question(q: Dict, index: int, filepath: str, global_ids: Set[str]) -> List[str]:
    """Validate a single question dict. Returns list of error messages."""
    errors = []
    rel_path = os.path.relpath(filepath, ROOT)
    location = f"{rel_path} item #{index}"

    if not isinstance(q, dict):
        return [f"{location}: question entry must be a YAML mapping/dict, got {type(q).__name__}"]

    qid = q.get("id")
    if not qid or not isinstance(qid, str) or not qid.strip():
        errors.append(f"{location}: missing or invalid 'id' (must be a non-empty string)")
    else:
        qid = qid.strip()
        location = f"{rel_path} ({qid})"
        if not ID_PATTERN.match(qid):
            errors.append(f"{location}: ID contains invalid characters (must match {ID_PATTERN.pattern})")
        if qid in global_ids:
            errors.append(f"{location}: duplicate question ID '{qid}' found across suites")
        else:
            global_ids.add(qid)

    question = q.get("question")
    if not question or not isinstance(question, str) or not question.strip():
        errors.append(f"{location}: missing or empty 'question' string")

    category = q.get("category")
    is_ambiguous = category == "ambiguous"
    gold_sql = q.get("gold_sql")

    if is_ambiguous:
        expected = q.get("expected")
        if not expected or not isinstance(expected, str) or not expected.strip():
            errors.append(f"{location}: ambiguous question must define a non-empty 'expected' explanation")
        if gold_sql is not None and not isinstance(gold_sql, str):
            errors.append(f"{location}: 'gold_sql' for ambiguous question must be null or string")
    else:
        if not gold_sql or not isinstance(gold_sql, str) or not gold_sql.strip():
            errors.append(f"{location}: missing or empty 'gold_sql' query")
        else:
            stripped_sql = gold_sql.strip().lower()
            if not any(stripped_sql.startswith(prefix) for prefix in VALID_SQL_PREFIXES):
                errors.append(
                    f"{location}: 'gold_sql' must start with one of {VALID_SQL_PREFIXES}, got: {gold_sql[:30]!r}"
                )

    if "ordered" in q and not isinstance(q["ordered"], bool):
        errors.append(f"{location}: 'ordered' must be a boolean (True/False), got {type(q['ordered']).__name__}")

    return errors


def validate_file(filepath: str, global_ids: Set[str]) -> Tuple[int, List[str]]:
    """Validate a YAML question file. Returns (count_of_questions, errors)."""
    errors: List[str] = []
    if not os.path.exists(filepath):
        return 0, [f"File not found: {filepath}"]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return 0, [f"YAML parsing error in {filepath}: {exc}"]

    if data is None:
        return 0, [f"File is empty: {filepath}"]

    if not isinstance(data, list):
        return 0, [f"Root of {filepath} must be a YAML list, got {type(data).__name__}"]

    for idx, item in enumerate(data, start=1):
        errs = validate_question(item, idx, filepath, global_ids)
        errors.extend(errs)

    return len(data), errors


def validate_suites(files: List[str]) -> bool:
    """Validate all question suite files. Returns True if all pass, False otherwise."""
    global_ids: Set[str] = set()
    all_errors: List[str] = []
    summary: List[Tuple[str, int]] = []

    for filepath in files:
        count, errors = validate_file(filepath, global_ids)
        all_errors.extend(errors)
        rel_name = os.path.relpath(filepath, ROOT)
        summary.append((rel_name, count))

    if all_errors:
        print("[FAIL] Question suite validation failed with errors:")
        for err in all_errors:
            print(f"  - {err}")
        return False

    summary_str = ", ".join(f"{name} ({count})" for name, count in summary)
    total_questions = sum(count for _, count in summary)
    print(f"[PASS] Validated {total_questions} questions across {len(summary)} suites: {summary_str}.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Validate question YAML suites for dbeval")
    parser.add_argument(
        "files",
        nargs="*",
        default=DEFAULT_FILES,
        help="Question YAML files to validate (default: questions/appdb.yaml, questions/olist.yaml)",
    )
    args = parser.parse_args()

    files = [os.path.abspath(f) for f in args.files]
    success = validate_suites(files)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
