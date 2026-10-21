"""Promote draft questions to validated questions.

A question is VALIDATED only when three independent answers agree:
  1. your hand-written gold_sql
  2. an LLM "oracle" A (schema + business rules)
  3. an LLM "oracle" B (same inputs, different instructions, optional different model)

Disagreements go to questions/disputed/<db>.yaml. That folder is a finding, so keep it.

Run:
    python scorer/validate_gold.py --db appdb
    python scorer/validate_gold.py --db olist
    python scorer/validate_gold.py --db appdb --skip-oracle   # only check the hand-written SQL runs
    python scorer/validate_gold.py --db appdb --only appdb-017,appdb-020,appdb-025   # re-check just these
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


def oracle_sql(db, question, system, model=None):
    prompt = f"SCHEMA\n{b.schema_text(db)}\nBUSINESS RULES\n{rules_for(db)}\nQUESTION\n{question}\n\nSQL:"
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
    try:
        return b.run_sql(db, sql)[1], None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:200]}"


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
            try:
                sql = oracle_sql(args.db, q["question"], system, model)
                rows, err = try_run(args.db, sql) if b.looks_read_only(sql) else (None, "not a single SELECT")
            except Exception as e:
                sql, rows, err = None, None, f"{type(e).__name__}: {str(e)[:200]}"
            ok = rows is not None and same(gold_rows, rows, ordered)
            verdicts[name] = {"agrees": ok, "sql": sql, "error": err}

        if all(v["agrees"] for v in verdicts.values()):
            validated.append(q)
            print(f"{q['id']}: validated")
        else:
            q["oracles"] = verdicts
            disputed.append(q)
            who = [n for n, v in verdicts.items() if not v["agrees"]]
            print(f"{q['id']}: DISPUTED ({', '.join(who)} disagree)")

    out = os.path.join(ROOT, "questions", f"{args.db}.yaml")
    dis = os.path.join(ROOT, "questions", "disputed", f"{args.db}.yaml")
    os.makedirs(os.path.dirname(dis), exist_ok=True)

    if only is not None:  # merge with what is already on disk, replacing the re-checked ids
        def load(path):
            return yaml.safe_load(open(path, encoding="utf-8")) or [] if os.path.exists(path) else []
        redone = {q["id"] for q in validated + disputed}
        validated = [q for q in load(out) if q["id"] not in redone] + validated
        disputed = [q for q in load(dis) if q["id"] not in redone] + disputed
        validated.sort(key=lambda q: q["id"])
        disputed.sort(key=lambda q: q["id"])
    yaml.safe_dump(validated, open(out, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    yaml.safe_dump(disputed, open(dis, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    print(f"\nvalidated: {len(validated)}   disputed: {len(disputed)}")
    print(f"wrote {out}\nwrote {dis}")


if __name__ == "__main__":
    main()
