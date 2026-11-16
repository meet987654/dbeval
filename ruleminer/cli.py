"""Command-line interface for RuleMiner:
Extracts business rules from schemas and query logs, and exports them in markdown or JSON.

Usage:
    python -m ruleminer.cli --db appdb --query-log questions/appdb.yaml --out docs/appdb_induced_rules.md
    python -m ruleminer.cli --db appdb --print

Export the rules to a semantic-layer format (see docs/ruleminer_export.md):
    python -m ruleminer.cli export --format dbt  --out dbt_models/  --min-confidence 0.9
    python -m ruleminer.cli export --format wren --out wren_models/ --db appdb --url duckdb:///db/appdb.duckdb
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUNNERS_DIR = os.path.join(ROOT, "runners")
if RUNNERS_DIR not in sys.path:
    sys.path.insert(0, RUNNERS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ruleminer import mine_rules
from ruleminer.query_log_miner import QueryLogMiner
from ruleminer.schema_signals import SchemaSignalExtractor
from ruleminer.synthesizer import RuleSynthesizer


def _connect(db, url=None):
    """Return a SQLAlchemy engine for `db` (explicit URL, the reader DB, or the local SQLite fixture), or None."""
    if url:
        from sqlalchemy import create_engine

        return create_engine(url)
    try:
        import baseline as b

        engine = b.reader_engine(db)
        with engine.connect():
            pass
        return engine
    except Exception:
        sqlite_file = os.path.join(ROOT, "db", f"{db}.sqlite")
        if os.path.exists(sqlite_file):
            from sqlalchemy import create_engine

            return create_engine(f"sqlite:///{sqlite_file}")
    return None


def _schema_of(engine):
    """{table: {column: type}} from the live database, or {} if it cannot be inspected."""
    if engine is None:
        return {}
    try:
        from sqlalchemy import inspect

        insp = inspect(engine)
        return {t: {c["name"]: str(c["type"]) for c in insp.get_columns(t)} for t in insp.get_table_names()}
    except Exception:
        pass
    # SQLAlchemy reflection fails on some dialects (e.g. duckdb-engine); information_schema works there
    try:
        from sqlalchemy import text

        out = {}
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT table_name, column_name, data_type FROM information_schema.columns "
                "WHERE table_schema NOT IN ('information_schema', 'pg_catalog') ORDER BY table_name, ordinal_position"
            ))
            for t, c, d in rows:
                out.setdefault(t, {})[c] = str(d)
        return out
    except Exception:
        return {}


def export_main(argv):
    """`export` subcommand: mine rules, then write them as dbt MetricFlow YAML or a Wren MDL manifest."""
    from ruleminer.export import export_files, filter_rules

    parser = argparse.ArgumentParser(
        prog="python -m ruleminer.cli export",
        description="Export mined business rules to dbt MetricFlow or Wren Engine definitions.",
    )
    parser.add_argument("--format", choices=["dbt", "wren"], required=True)
    parser.add_argument("--out", required=True, help="Output directory (created if missing)")
    parser.add_argument("--db", default="appdb")
    parser.add_argument("--url", default=None, help="SQLAlchemy URL to inspect (default: reader DB or db/<db>.sqlite)")
    parser.add_argument("--query-log", default=None, help="Query log (default: questions/<db>.yaml)")
    parser.add_argument("--min-support", type=float, default=0.5, help="Mining support threshold (default: 0.5)")
    parser.add_argument("--min-confidence", type=float, default=0.0,
                        help="Only export rules with confidence >= this value (default: 0.0, export all)")
    args = parser.parse_args(argv)

    query_log = args.query_log or os.path.join(ROOT, "questions", f"{args.db}.yaml")
    engine = _connect(args.db, args.url)
    schema = _schema_of(engine)
    synth = mine_rules(db=args.db, engine=engine, query_log_path=query_log, min_support=args.min_support)
    kept = filter_rules(synth.rules, args.min_confidence)

    files = export_files(args.format, synth.rules, schema or None, args.min_confidence)
    os.makedirs(args.out, exist_ok=True)
    for name, text in files.items():
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {os.path.join(args.out, name)}")
    print(f"Exported {len(kept)} of {len(synth.rules)} rules (min confidence {args.min_confidence}).")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "export":
        return export_main(argv[1:])
    parser = argparse.ArgumentParser(
        description="RuleMiner: Automated rule discovery from schemas and query logs."
    )
    parser.add_argument("--db", default="appdb", help="Target database name (default: appdb)")
    parser.add_argument(
        "--query-log",
        default=None,
        help="Path to query log file (YAML, JSON, or SQL). Defaults to questions/{db}.yaml if exists.",
    )
    parser.add_argument(
        "--min-support",
        type=float,
        default=0.5,
        help="Minimum support threshold for invariant predicates (default: 0.5)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument("--out", default=None, help="Output file path (optional)")
    parser.add_argument("--print", action="store_true", help="Print rules to standard output")
    parser.add_argument(
        "--show-signals",
        action="store_true",
        help="Print detailed schema signals and mining frequencies",
    )

    args = parser.parse_args(argv)

    # Determine query log path
    query_log = args.query_log
    if not query_log:
        default_ql = os.path.join(ROOT, "questions", f"{args.db}.yaml")
        if os.path.exists(default_ql):
            query_log = default_ql

    # Try connecting to engine if available
    engine = None
    try:
        import baseline as b

        engine = b.reader_engine(args.db)
        with engine.connect() as conn:
            pass
    except Exception:
        # Fallback to local SQLite fixture if present
        sqlite_file = os.path.join(ROOT, "db", f"{args.db}.sqlite")
        if os.path.exists(sqlite_file):
            from sqlalchemy import create_engine

            engine = create_engine(f"sqlite:///{sqlite_file}")

    extractor = SchemaSignalExtractor()
    signals = []
    if engine is not None:
        try:
            signals = extractor.extract_from_engine(engine, db_name=args.db)
        except Exception as e:
            if args.show_signals:
                print(f"[Warning] Failed to inspect live database: {e}", file=sys.stderr)

    miner = QueryLogMiner(min_support=args.min_support)
    mining_results = None
    if query_log and os.path.exists(query_log):
        mining_results = miner.mine_file(query_log)

    synth = RuleSynthesizer(schema_signals=signals, mining_results=mining_results)
    rules = synth.synthesize()

    if args.show_signals:
        print(f"=== Schema Signals ({len(signals)}) ===")
        for s in signals:
            print(f"- [{s.signal_type}] {s.table}.{s.column}: {s.description} (conf: {s.confidence})")
        print("\n=== Mining Invariants ===")
        if mining_results:
            for inv in mining_results.invariants:
                print(f"- {inv.predicate_sql} (support: {inv.support:.2f}, {inv.occurrences}/{inv.table_queries})")
            print("\n=== Discovered Joins ===")
            for j in mining_results.joins:
                print(f"- {j.join_sql} (occurrences: {j.occurrences})")
        print("========================\n")

    if args.format == "markdown":
        output = synth.to_markdown(db_name=args.db)
    elif args.format == "json":
        output = synth.to_json()
    else:
        output = synth.to_yaml()

    if args.out:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {len(rules)} synthesized rules to {args.out}")

    if args.print or not args.out:
        print(output)


if __name__ == "__main__":
    main()
