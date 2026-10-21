"""ktx runner: provides ktx-inferred semantic layer schema and relationships.

Usage:
    python runners/ktx_run.py --db olist --question "How many orders are there?"
    python runners/ktx_run.py --smoke questions/smoke.yaml
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import baseline as b  # reuses database connection, execution, and LLM calling

SYSTEM_PROMPT = (
    "You are a careful PostgreSQL analyst. You are provided with a database schema and an "
    "automatically inferred semantic layer containing verified cross-table joins. "
    "Given a business question, write ONE read-only PostgreSQL query that answers it. "
    "Use the inferred joins when joining tables. Return only the SQL, with no explanation and no markdown."
)

_CACHE = {}

def get_ktx_schema_path(db):
    if db == "olist":
        return os.path.join(ROOT, "layers", "ktx", "olist", "semantic-layer", "olist", "_schema", "public.yaml")
    elif db == "appdb":
        return os.path.join(ROOT, "layers", "ktx", "appdb_v2", "semantic-layer", "appdb", "_schema", "public.yaml")
    raise ValueError(f"Unknown database: {db}")

def ktx_context_text(db):
    if db in _CACHE:
        return _CACHE[db]

    path = get_ktx_schema_path(db)
    if not os.path.exists(path):
        raise FileNotFoundError(f"ktx layer not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    lines = []
    lines.append(f"DATABASE: {db}")
    lines.append("TABLE SCHEMAS:")

    tables = data.get("tables", {})
    all_joins = []

    for t_name, t_meta in sorted(tables.items()):
        cols = t_meta.get("columns", [])
        col_strs = [f"{c['name']} ({c.get('type', 'unknown')})" for c in cols]
        lines.append(f"  TABLE {t_name} (\n    " + ",\n    ".join(col_strs) + "\n  )")

        for j in t_meta.get("joins", []):
            all_joins.append({
                "from_table": t_name,
                "to_table": j.get("to"),
                "on": j.get("on"),
                "relationship": j.get("relationship", "unknown"),
                "source": j.get("source", "inferred")
            })

    lines.append("\nINFERRED RELATIONSHIPS / JOINS:")
    seen_edges = set()
    for j in all_joins:
        on_expr = j["on"]
        if on_expr:
            m = re.match(r'([\w\.]+)\s*=\s*([\w\.]+)', on_expr)
            if m:
                edge = tuple(sorted([m.group(1).replace("public.", ""), m.group(2).replace("public.", "")]))
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    lines.append(f"  {edge[0]} = {edge[1]}  [{j['relationship']}, {j['source']}]")

    ctx = "\n".join(lines)
    _CACHE[db] = ctx
    return ctx

def answer(db, question):
    started = time.time()
    result = {
        "system": "ktx",
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
        context = ktx_context_text(db)
        user_prompt = f"KTX INFERRED SEMANTIC LAYER\n{context}\n\nQUESTION\n{question}\n\nSQL:"
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
    print(f"[KTX | {r['db']}] {r['question']}")
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
        print(ktx_context_text(args.db))
    elif args.smoke:
        out = []
        with open(args.smoke, encoding="utf-8") as f:
            for item in yaml.safe_load(f):
                r = answer(item["db"], item["question"])
                show(r)
                out.append(r)
        os.makedirs("results/raw", exist_ok=True)
        with open("results/raw/smoke_ktx.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print("\nSaved results/raw/smoke_ktx.json")
    elif args.db and args.question:
        show(answer(args.db, args.question))
    else:
        ap.print_help()
