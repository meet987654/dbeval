"""Promote draft questions to validated questions.

A question is VALIDATED when your hand-written gold_sql and the LLM oracles agree:
  1. your hand-written gold_sql
  2. LLM "oracle" A (schema + business rules)
  3. LLM "oracle" B (same inputs, different instructions, optional different model)

How disagreements are handled:
  - An oracle whose SQL FAILS gets one repair attempt (the error is shown to it).
    If it still fails, it ABSTAINS. An abstaining oracle is not counted as a disagreement,
    but at least one oracle must still agree with the gold answer.
  - If an oracle returns a valid but different answer, the question is DISPUTED
    (questions/disputed/<db>.yaml). Read it: sometimes the gold is wrong, sometimes the
    question is vague, sometimes the oracle misread it.
  - A human can settle a dispute by editing the draft: set `adjudicated: true` and
    `adjudication_reason: ...`. The question is then validated, and the reason is kept in the
    file. Report how many questions were adjudicated by hand.

Run:
    python scorer/validate_gold.py --db appdb
    python scorer/validate_gold.py --db olist --skip-oracle   # only check the hand-written SQL runs
    python scorer/validate_gold.py --db olist --only olist-012,olist-016   # re-check just these
                                                # (merges into the existing validated/disputed files)

Reads : questions/drafts/<db>.yaml, docs/business_rules.md
Writes: questions/<db>.yaml (validated), questions/disputed/<db>.yaml
Optional .env: GOLD_MODEL_B=<a different model for oracle B>
"""

import argparse
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, HERE)

import baseline as b  # noqa: E402
from compare import same  # noqa: E402

PROMPT_A = (
    "You are a careful PostgreSQL analyst. Write ONE read-only PostgreSQL query that answers the "
    "question. Follow the BUSINESS RULES exactly. Return only the SQL."
)
PROMPT_B = (
    "You are a senior data engineer reviewing metric definitions. Before writing SQL, silently "
    "list which BUSINESS RULES apply to the question and what could double count rows. Then "
    "output ONLY one read-only PostgreSQL query that answers the question under those rules."
)


def rules_for(db):
    text = open(os.path.join(ROOT, "docs", "business_rules.md"), encoding="utf-8").read()
    parts = re.split(r"^## ", text, flags=re.MULTILINE)
    for part in parts:
        if part.lower().startswith(db):
            return part
    return ""


def ask_oracle(db, question, system, model=None, bad_sql=None, error=None):
    prompt = f"SCHEMA\n{b.schema_text(db)}\nBUSINESS RULES\n{rules_for(db)}\nQUESTION\n{question}\n"
    if bad_sql:
        prompt += (f"\nYOUR PREVIOUS SQL\n{bad_sql}\nIT FAILED WITH\n{error}\n"
                   "Return a corrected single query.\n")
    prompt += "\nSQL:"
    old = os.environ.get("LLM_MODEL")
    if model:
        os.environ["LLM_MODEL"] = model
    try:
        raw, _, _ = b.call_llm(system, prompt)
    finally:
        if old is not None:
            os.environ["LLM_MODEL"] = old
    return b.extract_sql(raw)


def try_run(db, sql):
    if not b.looks_read_only(sql):
        return None, "not a single SELECT/WITH statement"
    try:
        return b.run_sql(db, sql)[1], None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:200]}"


def run_oracle(db, question, system, model, gold_rows, ordered):
    """Returns a verdict dict with status: agrees | differs | abstain."""
    sql = rows = err = None
    try:
        sql = ask_oracle(db, question, system, model)
        rows, err = try_run(db, sql)
        repaired = False
        if err:  # one repair attempt, showing the error
            sql = ask_oracle(db, question, system, model, bad_sql=sql, error=err)
            rows, err = try_run(db, sql)
            repaired = True
    except Exception as e:
        return {"status": "abstain", "sql": sql, "error": f"{type(e).__name__}: {str(e)[:200]}"}
    if err:
        return {"status": "abstain", "sql": sql, "error": err, "repaired": repaired}
    status = "agrees" if same(gold_rows, rows, ordered) else "differs"
    return {"status": status, "sql": sql, "error": None, "repaired": repaired}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, choices=["olist", "appdb"])
    ap.add_argument("--skip-oracle", action="store_true")
    ap.add_argument("--only", help="comma-separated question ids to (re)validate and merge into the existing files")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",")} if args.only else None

    drafts = yaml.safe_load(open(os.path.join(ROOT, "questions", "drafts", f"{args.db}.yaml"), encoding="utf-8"))
    validated, disputed = [], []

    for q in drafts:
        q = dict(q)
        if only is not None and q["id"] not in only:
            continue
        if q.get("category") == "ambiguous":
            validated.append(q)
            print(f"{q['id']}: ambiguous (kept, scored separately)")
            continue

        gold_rows, err = try_run(args.db, q["gold_sql"])
        if err:
            q["reason"] = f"hand-written gold SQL failed: {err}"
            disputed.append(q)
            print(f"{q['id']}: DISPUTED (gold SQL error)")
            continue

        if args.skip_oracle:
            validated.append(q)
            print(f"{q['id']}: gold runs ({len(gold_rows)} rows), oracles skipped")
            continue

        ordered = bool(q.get("ordered"))
        verdicts = {}
        for name, system, model in [("oracle_a", PROMPT_A, None), ("oracle_b", PROMPT_B, os.getenv("GOLD_MODEL_B"))]:
            verdicts[name] = run_oracle(args.db, q["question"], system, model, gold_rows, ordered)

        statuses = [v["status"] for v in verdicts.values()]
        q["oracles"] = verdicts
        if "differs" not in statuses and "agrees" in statuses:
            note = " (one oracle abstained)" if "abstain" in statuses else ""
            validated.append({k: v for k, v in q.items() if k != "oracles"})
            print(f"{q['id']}: validated{note}")
        elif q.get("adjudicated"):
            validated.append({k: v for k, v in q.items() if k != "oracles"})
            print(f"{q['id']}: validated by hand adjudication")
        else:
            disputed.append(q)
            who = [n for n, v in verdicts.items() if v["status"] != "agrees"]
            print(f"{q['id']}: DISPUTED ({', '.join(who)} did not agree)")

    out = os.path.join(ROOT, "questions", f"{args.db}.yaml")
    dis = os.path.join(ROOT, "questions", "disputed", f"{args.db}.yaml")
    os.makedirs(os.path.dirname(dis), exist_ok=True)

    if only is not None:  # merge with what is already on disk, replacing the re-checked ids
        def load(path):
            return (yaml.safe_load(open(path, encoding="utf-8")) or []) if os.path.exists(path) else []
        redone = {q["id"] for q in validated + disputed}
        validated = [q for q in load(out) if q["id"] not in redone] + validated
        disputed = [q for q in load(dis) if q["id"] not in redone] + disputed
        validated.sort(key=lambda q: q["id"])
        disputed.sort(key=lambda q: q["id"])

    yaml.safe_dump(validated, open(out, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    yaml.safe_dump(disputed, open(dis, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    adj = sum(1 for q in validated if q.get("adjudicated"))
    print(f"\nvalidated: {len(validated)} (hand-adjudicated: {adj})   disputed: {len(disputed)}")
    print(f"wrote {out}\nwrote {dis}")


if __name__ == "__main__":
    main()
