"""RuleMiner runner for dbeval:
Executes evaluation questions against schemas enriched with automatically discovered business rules.
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUNNERS_DIR = os.path.join(ROOT, "runners")
if RUNNERS_DIR not in sys.path:
    sys.path.insert(0, RUNNERS_DIR)

import baseline as b
from ruleminer import mine_rules

_INDUCED_RULES_CACHE = {}


def get_induced_rules_text(db: str, min_support: float = 0.5, force_refresh: bool = False) -> str:
    """Retrieve or generate induced business rules for a target database."""
    if not force_refresh and db in _INDUCED_RULES_CACHE:
        return _INDUCED_RULES_CACHE[db]

    rules_dir = os.path.join(HERE, "rules")
    os.makedirs(rules_dir, exist_ok=True)
    rule_file = os.path.join(rules_dir, f"{db}_induced.md")

    if not force_refresh and os.path.exists(rule_file):
        with open(rule_file, "r", encoding="utf-8") as f:
            content = f.read()
            _INDUCED_RULES_CACHE[db] = content
            return content

    # Discover rules automatically
    query_log = os.path.join(ROOT, "questions", f"{db}.yaml")
    engine = None
    try:
        engine = b.reader_engine(db)
        with engine.connect() as conn:
            pass
    except Exception:
        sqlite_file = os.path.join(ROOT, "db", f"{db}.sqlite")
        if os.path.exists(sqlite_file):
            from sqlalchemy import create_engine

            engine = create_engine(f"sqlite:///{sqlite_file}")

    synth = mine_rules(db=db, engine=engine, query_log_path=query_log, min_support=min_support)
    markdown_rules = synth.to_markdown(db_name=db)

    with open(rule_file, "w", encoding="utf-8") as f:
        f.write(markdown_rules)

    _INDUCED_RULES_CACHE[db] = markdown_rules
    return markdown_rules


def answer_ruleminer_rules(db: str, question: str):
    """Answer question using baseline schema plus automatically induced RuleMiner rules."""
    started = time.time()
    result = {
        "system": "ruleminer_rules",
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
        schema = b.schema_text(db)
        induced_rules = get_induced_rules_text(db)
        prompt = (
            f"SCHEMA & SEMANTIC LAYER\n{schema}\n\n"
            f"BUSINESS RULES & INSTRUCTIONS (AUTOMATICALLY DISCOVERED BY RULEMINER):\n{induced_rules}\n\n"
            f"QUESTION\n{question}\n\nSQL:"
        )

        system_prompt = (
            "You are a careful PostgreSQL analyst. Given a business question, write ONE read-only "
            "PostgreSQL query that answers it. Return only the SQL, with no explanation and no markdown."
        )

        raw, t_in, t_out = b.call_llm(system_prompt, prompt)
        result["tokens_in"], result["tokens_out"] = t_in, t_out
        result["context_tokens"] = len(prompt) // 4
        sql = b.extract_sql(raw)
        result["sql"] = sql

        if not b.looks_read_only(sql):
            raise ValueError("Refused: not a single SELECT/WITH statement")

        result["columns"], result["rows"] = b.run_sql(db, sql)
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:300]}"

    result["seconds"] = round(time.time() - started, 2)
    return result
