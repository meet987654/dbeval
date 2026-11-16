"""Helpers for multi-turn (conversational) question suites.

A conversation entry in a questions YAML file has `turns` instead of `question` / `gold_sql`:

    - id: appdb-conv-001
      category: conversation
      turns:
        - question: How many accounts do we have?
          gold_sql: SELECT ...
        - question: How many of those are on the scale plan?
          gold_sql: SELECT ...

Each turn is scored independently against its own gold SQL. The system under test sees the earlier
turns as its OWN prior questions and SQL (not the gold), so one wrong turn can mislead the next,
exactly as in a real conversation. This works with every runner because the history is folded into
the question text; no runner needs to know about conversations.
"""


def turn_id(conv_id, n):
    """Stable id for turn `n` (1-based) of a conversation, used as the CSV question id."""
    return f"{conv_id}#t{n}"


def contextualize(question, history):
    """Return `question` prefixed with the conversation so far.

    `history` is a list of (question, sql_or_None) for the earlier turns, oldest first.
    With no history the question is returned unchanged.
    """
    if not history:
        return question
    lines = ["This is a follow-up in a conversation. Earlier turns (your previous questions and SQL):"]
    for i, (q, sql) in enumerate(history, start=1):
        lines.append(f"Turn {i} question: {q}")
        lines.append(f"Turn {i} SQL: {sql if sql else '(no SQL was produced)'}")
    lines.append("")
    lines.append(f"Current question (it may refer to the earlier turns): {question}")
    return "\n".join(lines)


def expand(entries):
    """Flatten question entries into per-turn dicts.

    Single-turn entries pass through with `conv_id=None, turn=None`. A conversation yields one dict
    per turn with keys id, category, question, gold_sql, ordered, conv_id, turn.
    """
    out = []
    for q in entries:
        if "turns" not in q:
            out.append({**q, "conv_id": None, "turn": None})
            continue
        for n, t in enumerate(q["turns"], start=1):
            out.append({
                "id": turn_id(q["id"], n),
                "category": q.get("category", "conversation"),
                "question": t["question"],
                "gold_sql": t.get("gold_sql"),
                "ordered": bool(t.get("ordered", False)),
                "conv_id": q["id"],
                "turn": n,
            })
    return out


def conversation_results(records):
    """Group per-turn records into whole conversations.

    Returns {(system, db, run_num, conv_id): [passed per turn, in turn order]}. Single-turn records are ignored.
    """
    grouped = {}
    for r in records:
        qid = str(r["question_id"])
        if "#t" not in qid:
            continue
        conv_id, _, turn = qid.rpartition("#t")
        grouped.setdefault((r["system"], r["db"], r["run_num"], conv_id), []).append((int(turn), bool(r["passed"])))
    return {k: [p for _, p in sorted(v)] for k, v in grouped.items()}
