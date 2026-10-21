"""Wren Engine runner: provides Wren Engine MDL compiled models and relationships context.

Usage:
    python runners/wren_run.py --db olist --question "How many orders are there?"
    python runners/wren_run.py --smoke questions/smoke.yaml
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
    "You are a careful PostgreSQL analyst. You are provided with a database semantic layer "
    "compiled in Wren Engine Modeling Definition Language (MDL), including validated models and relationships. "
    "Given a business question, write ONE read-only PostgreSQL query that answers it. "
    "Use the declared relationships when joining models. Return only the SQL, with no explanation and no markdown."
)

_CACHE = {}

def get_wren_mdl_path(db):
    if db == "olist":
        return os.path.join(ROOT, "layers", "wren", "olist", "target", "mdl.json")
    elif db == "appdb":
        return os.path.join(ROOT, "layers", "wren", "appdb_v2", "target", "mdl.json")
    raise ValueError(f"Unknown database: {db}")

def wren_context_text(db):
    if db in _CACHE:
        return _CACHE[db]

    path = get_wren_mdl_path(db)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Wren MDL file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        mdl = json.load(f)

    lines = [f"DATABASE: {db}", "WREN ENGINE COMPILED SEMANTIC LAYER (MDL):"]
    lines.append("\nMODELS:")
    for model in sorted(mdl.get("models", []), key=lambda m: m["name"]):
        m_name = model["name"]
        cols = model.get("columns", [])
        col_strs = []
        for c in cols:
            flags = []
            if c.get("isPrimaryKey"):
                flags.append("PRIMARY KEY")
            if c.get("notNull"):
                flags.append("NOT NULL")
            flag_str = f", {', '.join(flags)}" if flags else ""
            col_strs.append(f"{c['name']} ({c.get('type', 'VARCHAR')}{flag_str})")
        lines.append(f"  MODEL {m_name} (\n    " + ",\n    ".join(col_strs) + "\n  )")

    relationships = mdl.get("relationships", [])
    lines.append("\nRELATIONSHIPS:")
    if relationships:
        for r in relationships:
            cond = r.get("condition", "")
            j_type = r.get("joinType", "MANY_TO_ONE")
            name = r.get("name", "")
            lines.append(f"  {cond}  [{j_type}, {name}]")
    else:
        lines.append("  (No explicit foreign keys / relationships declared in schema)")

    ctx = "\n".join(lines)
    _CACHE[db] = ctx
    return ctx

def answer(db, question):
    started = time.time()
    result = {
        "system": "wren",
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
        context = wren_context_text(db)
        user_prompt = f"WREN ENGINE SEMANTIC LAYER (MDL)\n{context}\n\nQUESTION\n{question}\n\nSQL:"
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
    print(f"[WREN | {r['db']}] {r['question']}")
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
        print(wren_context_text(args.db))
    elif args.smoke:
        out = []
        with open(args.smoke, encoding="utf-8") as f:
            for item in yaml.safe_load(f):
                r = answer(item["db"], item["question"])
                show(r)
                out.append(r)
        os.makedirs("results/raw", exist_ok=True)
        with open("results/raw/smoke_wren.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print("\nSaved results/raw/smoke_wren.json")
    elif args.db and args.question:
        show(answer(args.db, args.question))
    else:
        ap.print_help()
