"""Decide whether a tool's answer matches the gold answer.

Rules:
  - Row order is ignored, unless the question is marked `ordered: true`.
  - Numbers match if equal after rounding to 2 decimals (5, 5.0 and Decimal('5.00') match).
  - Column NAMES are ignored, and column order is ignored.
  - EXTRA columns in the tool's answer are allowed (a tool that returns the
    tier AND its count still passes "which tier has the most...").
  - Every gold column must appear in the answer, with the values lined up row by row.
"""

from datetime import date, datetime
from decimal import Decimal
from itertools import product


def norm(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float, Decimal)):
        return f"{round(float(v), 2):.2f}"
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    s = str(v).strip()
    try:  # a number that arrived as text
        return f"{round(float(s), 2):.2f}"
    except ValueError:
        return s


def _columns(rows):
    return [[norm(v) for v in col] for col in zip(*rows)]


def same(gold_rows, cand_rows, ordered=False):
    gold_rows, cand_rows = list(gold_rows), list(cand_rows)
    if len(gold_rows) != len(cand_rows):
        return False
    if not gold_rows:
        return True
    gcols, ccols = _columns(gold_rows), _columns(cand_rows)
    if len(ccols) < len(gcols):
        return False

    def key(col):
        return col if ordered else sorted(col)

    ckeys = [key(c) for c in ccols]
    options = [[j for j, ck in enumerate(ckeys) if ck == key(g)] for g in gcols]
    if any(not o for o in options):
        return False

    gold_set = list(zip(*gcols))
    for combo in product(*options):
        if len(set(combo)) != len(combo):
            continue
        projected = list(zip(*[ccols[j] for j in combo]))
        if ordered:
            if projected == gold_set:
                return True
        elif sorted(projected) == sorted(gold_set):
            return True
    return False
