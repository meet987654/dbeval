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
    "You are a careful PostgreSQL analyst. Given a business question, write ONE read-only PostgreSQL query that answers it. "
    "Return only the SQL, with no explanation and no markdown."
)

_CACHE = {}

def get_wren_mdl_path(db, reviewed=False):
    if reviewed:
        return os.path.join(ROOT, "layers", "wren", f"{db}_reviewed", "target", "mdl.json")
    if db == "olist":
        return os.path.join(ROOT, "layers", "wren", "olist", "target", "mdl.json")
    elif db == "appdb":
        return os.path.join(ROOT, "layers", "wren", "appdb_v2", "target", "mdl.json")
    raise ValueError(f"Unknown database: {db}")

def wren_context_text(db, reviewed=False):
    cache_key = f"{db}_reviewed" if reviewed else db
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    path = get_wren_mdl_path(db, reviewed=reviewed)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Wren MDL file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        mdl = json.load(f)

    lines = [f"DATABASE: {db}", "WREN ENGINE COMPILED SEMANTIC LAYER (MDL):"]

    # Global / Schema-level instructions or rules
    instructions = mdl.get("instructions") or mdl.get("rules") or []
    inst_file = os.path.join(os.path.dirname(os.path.dirname(path)), "instructions.md")
    if not instructions and os.path.exists(inst_file):
        try:
            with open(inst_file, "r", encoding="utf-8") as f:
                inst_text = f.read().strip()
            if inst_text:
                instructions = [inst_text]
        except Exception:
            pass

    if instructions:
        lines.append("\nBUSINESS RULES & INSTRUCTIONS:")
        if isinstance(instructions, list):
            for inst in instructions:
                lines.append(f"  - {inst}")
        else:
            lines.append(f"  {instructions}")

    lines.append("\nMODELS & SCHEMAS:")
    for model in sorted(mdl.get("models", []), key=lambda m: m["name"]):
        m_name = model["name"]
        m_desc = model.get("description") or model.get("properties", {}).get("description", "")
        desc_str = f" -- {m_desc}" if m_desc else ""
        lines.append(f"  MODEL {m_name}{desc_str} (")
        cols = model.get("columns", [])
        col_strs = []
        for c in cols:
            parts = [c["name"], f"({c.get('type', 'VARCHAR')})"]
            if c.get("isPrimaryKey"):
                parts.append("[PRIMARY KEY]")
            if c.get("notNull"):
                parts.append("[NOT NULL]")
            if c.get("isCalculated") and c.get("expression"):
                parts.append(f"[CALCULATED: {c['expression']}]")
            c_desc = c.get("description") or c.get("properties", {}).get("description", "")
            if c_desc:
                parts.append(f"-- {c_desc}")
            col_strs.append("    " + " ".join(parts))
        lines.append(",\n".join(col_strs))
        lines.append("  )")

    # Views
    views = mdl.get("views", [])
    if views:
        lines.append("\nVIEWS & VIRTUAL TABLES:")
        for v in views:
            v_name = v.get("name", "")
            v_desc = v.get("description") or v.get("properties", {}).get("description", "")
            desc_str = f" -- {v_desc}" if v_desc else ""
            lines.append(f"  VIEW {v_name}{desc_str}:")
            stmt = v.get("statement") or v.get("sql", "")
            if stmt:
                lines.append(f"    SQL: {stmt.strip()}")

    # Metrics
    metrics = mdl.get("metrics", []) + mdl.get("cumulativeMetrics", [])
    if metrics:
        lines.append("\nMETRICS & MEASURES:")
        for m in metrics:
            m_name = m.get("name", "")
            m_model = m.get("baseModel", "")
            m_measure = m.get("measure", "")
            m_desc = m.get("description") or m.get("properties", {}).get("description", "")
            desc_str = f" ({m_desc})" if m_desc else ""
            lines.append(f"  - {m_name} ON {m_model}: {m_measure}{desc_str}")

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

    ctx = "\n".join(lines).strip()
    _CACHE[db] = ctx
    return ctx

def answer(db, question, reviewed=False):
    started = time.time()
    result = {
        "system": "wren_reviewed" if reviewed else "wren",
        "db": db,
        "question": question,
        "sql": None,
        "columns": [],
        "rows": [],
        "error": None,
        "tokens_in": 0,
        "tokens_out": 0,
        "context_tokens": 0,
        "seconds": 0.0,
    }
    try:
        context = wren_context_text(db, reviewed=reviewed)
        user_prompt = f"SCHEMA & SEMANTIC LAYER\n{context}\n\nQUESTION\n{question}\n\nSQL:"
        raw, t_in, t_out = b.call_llm(SYSTEM_PROMPT, user_prompt)
        result["tokens_in"], result["tokens_out"] = t_in, t_out
        result["context_tokens"] = len(context) // 4
        sql = b.extract_sql(raw)
        result["sql"] = sql
        if not b.looks_read_only(sql):
            raise ValueError("Refused: not a single SELECT/WITH statement")
        result["columns"], result["rows"] = b.run_sql(db, sql)
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    result["seconds"] = round(time.time() - started, 2)
    return result

def answer_reviewed(db, question):
    return answer(db, question, reviewed=True)

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
