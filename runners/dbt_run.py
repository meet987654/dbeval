"""dbt Semantic Layer (MetricFlow) runner: gives the model the dbt semantic models and metrics
(YAML spec) as context, then executes the SQL it writes against the database.

The semantic layer lives in layers/dbt/<db>/semantic_models.yml. The MetricFlow CLI is not
required: like the other runners, the layer is rendered into the prompt as context.

Usage:
    python runners/dbt_run.py --db appdb --question "How many active subscriptions do we have?"
    python runners/dbt_run.py --db appdb --show-context
"""

import argparse
import os
import sys
import time

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import baseline as b  # reuses database connection, execution, and LLM calling

SYSTEM_PROMPT = (
    "You are a careful PostgreSQL analyst. Given a business question, write ONE read-only PostgreSQL query that answers it. "
    "Use the dbt semantic models and metrics as the source of truth for business definitions: apply the filters "
    "that the metrics define. Return only the SQL, with no explanation and no markdown."
)

_CACHE = {}


def dbt_layer_path(db):
    return os.path.join(ROOT, "layers", "dbt", db, "semantic_models.yml")


def load_layer(db):
    """Parse the dbt semantic layer YAML for `db`. Raises ValueError if there is none."""
    path = dbt_layer_path(db)
    if not os.path.exists(path):
        raise ValueError(f"No dbt semantic layer for database {db!r} (expected {path})")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def render_context(layer):
    """Render a parsed dbt semantic layer as compact, readable prompt text."""
    lines = ["DBT SEMANTIC MODELS:"]
    for sm in layer.get("semantic_models", []):
        desc = f" -- {sm['description']}" if sm.get("description") else ""
        table = str(sm.get("model", "")).replace("ref('", "").replace("')", "")
        lines.append(f"  SEMANTIC MODEL {sm['name']} (table {table}){desc}")
        for e in sm.get("entities", []):
            lines.append(f"    entity {e['name']} [{e['type']}] = {e.get('expr', e['name'])}")
        for d in sm.get("dimensions", []):
            note = f" -- {d['description']}" if d.get("description") else ""
            lines.append(f"    dimension {d['name']} [{d['type']}]{note}")
        for m in sm.get("measures", []):
            note = f" -- {m['description']}" if m.get("description") else ""
            lines.append(f"    measure {m['name']} = {m['agg']}({m.get('expr', m['name'])}){note}")
    lines.append("\nDBT METRICS (the business definitions; their filters are rules you must apply):")
    for met in layer.get("metrics", []):
        tp = met.get("type_params", {})
        if met.get("type") == "derived":
            body = f"derived: {tp.get('expr')}"
        elif met.get("type") == "ratio":
            body = f"ratio: {tp.get('numerator')} / {tp.get('denominator')}"
        else:
            body = f"measure {tp.get('measure')}"
        lines.append(f"  - {met['name']}: {body}")
        if met.get("description"):
            lines.append(f"      {met['description']}")
        if met.get("filter"):
            lines.append(f"      filter: {met['filter']}")
    return "\n".join(lines)


def dbt_context_text(db):
    if db not in _CACHE:
        _CACHE[db] = render_context(load_layer(db))
    return _CACHE[db]


def answer(db, question):
    started = time.time()
    result = {
        "system": "dbt",
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
        context = dbt_context_text(db)
        schema = b.schema_text(db)
        user_prompt = (f"SCHEMA\n{schema}\n\n{context}\n\nQUESTION\n{question}\n\nSQL:")
        raw, t_in, t_out = b.call_llm(SYSTEM_PROMPT, user_prompt)
        result["tokens_in"], result["tokens_out"] = t_in, t_out
        result["context_tokens"] = len(user_prompt) // 4
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
    print(f"[DBT | {r['db']}] {r['question']}")
    print("-" * 70)
    print(r["sql"])
    if r["error"]:
        print(f"ERROR: {r['error']}")
    else:
        print(f"-> {len(r['rows'])} rows; columns={r['columns']}")
    print(f"({r['seconds']}s, {r['tokens_in']}+{r['tokens_out']} tokens)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="appdb")
    ap.add_argument("--question")
    ap.add_argument("--show-context", action="store_true", help="print the rendered semantic layer and exit")
    args = ap.parse_args()
    if args.show_context:
        print(dbt_context_text(args.db))
        return
    if not args.question:
        ap.error("--question is required unless --show-context is given")
    show(answer(args.db, args.question))


if __name__ == "__main__":
    main()
