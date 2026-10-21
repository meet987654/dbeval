"""Datus runner: provides Datus LanceDB RAG metadata and sampled values context.

Usage:
    python runners/datus_run.py --db olist --question "How many orders are there?"
    python runners/datus_run.py --smoke questions/smoke.yaml
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import baseline as b  # reuses database connection, execution, and LLM calling

SYSTEM_PROMPT = (
    "You are a careful PostgreSQL analyst. You are provided with a database schema and sampled values "
    "retrieved from a Datus LanceDB context index. "
    "Given a business question, write ONE read-only PostgreSQL query that answers it. "
    "Return only the SQL, with no explanation and no markdown."
)

_CACHE = {}

def get_datus_dir(db):
    if db == "olist":
        return os.path.join(ROOT, "layers", "datus", "olist")
    elif db == "appdb":
        return os.path.join(ROOT, "layers", "datus", "appdb_v2")
    raise ValueError(f"Unknown database: {db}")

def datus_context_text(db):
    if db in _CACHE:
        return _CACHE[db]

    base_dir = get_datus_dir(db)
    meta_path = os.path.join(base_dir, "schema_metadata.json")
    val_path = os.path.join(base_dir, "schema_value.json")

    if not os.path.exists(meta_path) or not os.path.exists(val_path):
        raise FileNotFoundError(f"Datus layer files missing in {base_dir}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)
    with open(val_path, "r", encoding="utf-8") as f:
        val_data = json.load(f)

    val_by_table = {item["table_name"]: item.get("sample_rows", "") for item in val_data}

    lines = [f"DATABASE: {db}", "DATUS CONTEXT LAYER (STORED TABLE DEFINITIONS & SAMPLED VALUES):"]
    for item in sorted(meta_data, key=lambda x: x["table_name"]):
        t_name = item["table_name"]
        lines.append(f"\n--- TABLE: {t_name} ---")
        lines.append(item.get("definition", "").strip())
        samples = val_by_table.get(t_name, "").strip()
        if samples:
            lines.append("Sample rows:")
            # limit sample rows to 3 rows for prompt economy
            sample_lines = samples.splitlines()[:4]
            lines.append("\n".join(sample_lines))

    ctx = "\n".join(lines)
    _CACHE[db] = ctx
    return ctx

def answer(db, question):
    started = time.time()
    result = {
        "system": "datus",
        "db": db,
        "question": question,
        "sql": None,
        "columns": [],
        "rows": [],
        "error": None,
        "tokens_in": 0,
        "tokens_out": 0,
        "seconds": 0.0,
    }
    try:
        context = datus_context_text(db)
        user_prompt = f"DATUS CONTEXT LAYER\n{context}\n\nQUESTION\n{question}\n\nSQL:"
        raw, t_in, t_out = b.call_llm(SYSTEM_PROMPT, user_prompt)
        result["tokens_in"], result["tokens_out"] = t_in, t_out
        sql = b.extract_sql(raw)
        result["sql"] = sql
        if not b.looks_read_only(sql):
            raise ValueError("Refused: not a single SELECT/WITH statement")
        result["columns"], result["rows"] = b.run_sql(db, sql)
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    result["seconds"] = round(time.time() - started, 2)
    return result

def show(r):
    print("=" * 70)
    print(f"[DATUS | {r['db']}] {r['question']}")
    print("-" * 70)
    print(r["sql"])
    if r["error"]:
        print("ERROR:", r["error"])
    else:
        print(r["columns"])
        for row in r["rows"][:5]:
            print(row)
        if len(r["rows"]) > 5:
            print(f"... {len(r['rows'])} rows total")
    print(f"({r['seconds']}s, {r['tokens_in']} in / {r['tokens_out']} out tokens)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", choices=["olist", "appdb"])
    ap.add_argument("--question")
    ap.add_argument("--smoke", help="path to a YAML file of {db, question} items")
    ap.add_argument("--show-context", action="store_true")
    args = ap.parse_args()

    if args.show_context and args.db:
        print(datus_context_text(args.db))
    elif args.smoke:
        out = []
        with open(args.smoke, encoding="utf-8") as f:
            for item in yaml.safe_load(f):
                r = answer(item["db"], item["question"])
                show(r)
                out.append(r)
        os.makedirs("results/raw", exist_ok=True)
        with open("results/raw/smoke_datus.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print("\nSaved results/raw/smoke_datus.json")
    elif args.db and args.question:
        show(answer(args.db, args.question))
    else:
        ap.print_help()
