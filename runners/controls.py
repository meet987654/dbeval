"""Control runners for dbeval:
1. schema_only: Column names and types only, no samples, no constraints.
2. schema_true_joins: Column names and types, plus true core joins from questions/true_joins.yaml.
3. baseline_rules: Baseline schema (with 3 sample values/col) plus docs/business_rules.md.

All three use the exact same standard prompt template and codestral-2508 answering pipeline.
"""

import os
import re
import sys
import time
import yaml
from sqlalchemy import text

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import baseline as b

SYSTEM_PROMPT = (
    "You are a careful PostgreSQL analyst. Given a business question, write ONE read-only PostgreSQL query that answers it. "
    "Return only the SQL, with no explanation and no markdown."
)

_CACHE_SCHEMA_ONLY = {}
_CACHE_TRUE_JOINS = {}
_CACHE_RULES = {}

def schema_only_text(db):
    if db in _CACHE_SCHEMA_ONLY:
        return _CACHE_SCHEMA_ONLY[db]

    engine = b.reader_engine(db)
    lines = []
    with engine.connect() as conn:
        cols = conn.execute(text("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)).fetchall()

        tables = {}
        for table, column, dtype in cols:
            tables.setdefault(table, []).append((column, dtype))

        for table, columns in sorted(tables.items()):
            lines.append(f"TABLE {table}")
            for column, dtype in columns:
                lines.append(f"  {column} {dtype}")
            lines.append("")

    ctx = "\n".join(lines).strip()
    _CACHE_SCHEMA_ONLY[db] = ctx
    return ctx

def true_joins_text(db):
    if db in _CACHE_TRUE_JOINS:
        return _CACHE_TRUE_JOINS[db]

    joins_path = os.path.join(ROOT, "questions", "true_joins.yaml")
    if not os.path.exists(joins_path):
        raise FileNotFoundError(f"Missing {joins_path}")

    with open(joins_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    joins = [j for j in data.get(db, []) if j.get("kind") == "core"]
    lines = []
    for j in joins:
        lines.append(f"  {j['a']} = {j['b']}")

    ctx = "\n".join(lines).strip()
    _CACHE_TRUE_JOINS[db] = ctx
    return ctx

def rules_for(db):
    if db in _CACHE_RULES:
        return _CACHE_RULES[db]

    rules_path = os.path.join(ROOT, "docs", "business_rules.md")
    if not os.path.exists(rules_path):
        return ""

    with open(rules_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    parts = re.split(r"^## ", text_content, flags=re.MULTILINE)
    for part in parts:
        if part.lower().startswith(db):
            ctx = part.strip()
            _CACHE_RULES[db] = ctx
            return ctx
    return ""

def _execute_runner(sys_name, db, question, user_prompt):
    started = time.time()
    result = {
        "system": sys_name,
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

def answer_schema_only(db, question):
    schema = schema_only_text(db)
    prompt = f"SCHEMA & SEMANTIC LAYER\n{schema}\n\nQUESTION\n{question}\n\nSQL:"
    return _execute_runner("schema_only", db, question, prompt)

def answer_schema_true_joins(db, question):
    schema = schema_only_text(db)
    joins = true_joins_text(db)
    prompt = f"SCHEMA & SEMANTIC LAYER\n{schema}\n\nRELATIONSHIPS / JOINS:\n{joins}\n\nQUESTION\n{question}\n\nSQL:"
    return _execute_runner("schema_true_joins", db, question, prompt)

def answer_baseline_rules(db, question):
    schema = b.schema_text(db)
    rules = rules_for(db)
    prompt = f"SCHEMA & SEMANTIC LAYER\n{schema}\n\nBUSINESS RULES & INSTRUCTIONS:\n{rules}\n\nQUESTION\n{question}\n\nSQL:"
    return _execute_runner("baseline_rules", db, question, prompt)
