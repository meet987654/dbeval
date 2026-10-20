"""Baseline runner: the plain LLM sees only the table definitions.

Run one question:
    python runners/baseline.py --db olist --question "How many orders are there?"

Run the Day 1 smoke questions (5 per database):
    python runners/baseline.py --smoke questions/smoke.yaml

Needs: pip install sqlalchemy psycopg2-binary pyyaml python-dotenv anthropic
       (or `openai` instead of `anthropic`)

.env settings (names only, put your real values in your own .env):
    LLM_PROVIDER=anthropic          # or openai
    LLM_MODEL=<one model for the whole project>
    ANTHROPIC_API_KEY=...           # or OPENAI_API_KEY=...
    READER_URL_OLIST=postgresql://reader:reader@localhost:5433/olist
    READER_URL_APPDB=postgresql://reader:reader@localhost:5433/appdb
"""

import argparse
import json
import os
import re
import time

from sqlalchemy import create_engine, text

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

ROW_LIMIT = 500
TIMEOUT_MS = 15000
SAMPLES_PER_COLUMN = 3

SYSTEM_PROMPT = (
    "You are a careful PostgreSQL analyst. Given a database schema with sample "
    "values and a business question, write ONE read-only PostgreSQL query that "
    "answers it. Return only the SQL, with no explanation and no markdown."
)


# ---------- database ----------

def make_engine(url):
    """Pick whichever Postgres driver is installed (psycopg2 or psycopg 3)."""
    if url.startswith("postgresql://"):
        try:
            import psycopg2  # noqa: F401

            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        except ImportError:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url)


def reader_engine(db):
    url = os.getenv(f"READER_URL_{db.upper()}") or f"postgresql://reader:reader@localhost:5433/{db}"
    return make_engine(url)


_schema_cache = {}


def schema_text(db):
    """Table definitions, keys, and a few sample values per column."""
    if db in _schema_cache:
        return _schema_cache[db]
    engine = reader_engine(db)
    lines = []
    with engine.connect() as conn:
        cols = conn.execute(
            text(
                "SELECT table_name, column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public' ORDER BY table_name, ordinal_position"
            )
        ).fetchall()
        keys = conn.execute(
            text(
                "SELECT conrelid::regclass::text, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE contype IN ('p', 'f') AND connamespace = 'public'::regnamespace "
                "ORDER BY 1"
            )
        ).fetchall()

        tables = {}
        for table, column, dtype in cols:
            tables.setdefault(table, []).append((column, dtype))

        for table, columns in tables.items():
            lines.append(f"TABLE {table}")
            for column, dtype in columns:
                # sample from the first 200 non-null rows only, so it is cheap on big tables
                sample_sql = (
                    f'SELECT DISTINCT v FROM (SELECT "{column}"::text AS v FROM "{table}" '
                    f'WHERE "{column}" IS NOT NULL LIMIT 200) s LIMIT {SAMPLES_PER_COLUMN}'
                )
                try:
                    samples = [str(r[0])[:40] for r in conn.execute(text(sample_sql))]
                except Exception:
                    conn.rollback()
                    samples = []
                lines.append(f"  {column} {dtype}  e.g. {samples}")
            for t, definition in keys:
                if t.strip('"') == table:
                    lines.append(f"  CONSTRAINT {definition}")
            lines.append("")
    _schema_cache[db] = "\n".join(lines)
    return _schema_cache[db]


def run_sql(db, sql):
    """Run one read-only statement with a timeout and a row limit."""
    engine = reader_engine(db)
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text(f"SET LOCAL statement_timeout = {TIMEOUT_MS}"))
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [tuple(r) for r in result.fetchmany(ROW_LIMIT)]
    return columns, rows


# ---------- LLM ----------

def call_llm(system, user):
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    model = os.environ["LLM_MODEL"]
    if provider == "anthropic":
        from anthropic import Anthropic

        r = Anthropic().messages.create(
            model=model, max_tokens=1200, temperature=0, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
    if provider in ("openai", "groq"):
        from openai import OpenAI

        api_key = os.getenv("GROQ_API_KEY") if provider == "groq" else os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if provider == "groq" and not base_url:
            base_url = "https://api.groq.com/openai/v1"

        client = OpenAI(api_key=api_key, base_url=base_url)
        r = client.chat.completions.create(
            model=model, temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        t_in = r.usage.prompt_tokens if r.usage else 0
        t_out = r.usage.completion_tokens if r.usage else 0
        return r.choices[0].message.content, t_in, t_out
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def extract_sql(raw):
    raw = raw.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if fenced:
        raw = fenced.group(1).strip()
    return raw.rstrip(";").strip()


def looks_read_only(sql):
    """Cheap guard on top of the read-only database role."""
    return bool(re.match(r"^\s*(select|with)\b", sql, re.IGNORECASE)) and ";" not in sql


# ---------- the one function every runner must have ----------

def answer(db, question):
    started = time.time()
    result = {"system": "baseline", "db": db, "question": question,
              "sql": None, "columns": [], "rows": [], "error": None,
              "tokens_in": 0, "tokens_out": 0, "seconds": 0.0}
    try:
        user_prompt = f"SCHEMA\n{schema_text(db)}\nQUESTION\n{question}\n\nSQL:"
        raw, t_in, t_out = call_llm(SYSTEM_PROMPT, user_prompt)
        result["tokens_in"], result["tokens_out"] = t_in, t_out
        sql = extract_sql(raw)
        result["sql"] = sql
        if not looks_read_only(sql):
            raise ValueError("Refused: not a single SELECT/WITH statement")
        result["columns"], result["rows"] = run_sql(db, sql)
    except Exception as e:  # keep going, the scorer counts this as a failure
        result["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    result["seconds"] = round(time.time() - started, 2)
    return result


def show(r):
    print("=" * 70)
    print(f"[{r['db']}] {r['question']}")
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
    ap.add_argument("--show-schema", action="store_true")
    args = ap.parse_args()

    if args.show_schema and args.db:
        print(schema_text(args.db))
    elif args.smoke:
        import yaml

        out = []
        with open(args.smoke, encoding="utf-8") as f:
            for item in yaml.safe_load(f):
                r = answer(item["db"], item["question"])
                show(r)
                out.append(r)
        os.makedirs("results/raw", exist_ok=True)
        with open("results/raw/smoke_baseline.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print("\nSaved results/raw/smoke_baseline.json")
    elif args.db and args.question:
        show(answer(args.db, args.question))
    else:
        ap.print_help()
