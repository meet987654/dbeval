"""Benchmark harness: executes question suites across context layers,
scores results against live gold SQL execution using scorer/compare.py,
and records comprehensive latency, token usage, and accuracy logs to CSV.

Usage:
    python scorer/run_suite.py --system baseline --db appdb --runs 1
    python scorer/run_suite.py --system all --db both --runs 3
    python scorer/run_suite.py --system ktx --db olist --only olist-001,olist-002
"""

import argparse
import csv
from datetime import datetime
import json
import os
import sys
import time
from pathlib import Path
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, HERE)

import baseline as b_runner
import ktx_run
import datus_run
import wren_run
import controls
from compare import same

BENCHMARK_SYSTEMS = ["baseline", "ktx", "datus", "wren"]
CONTROL_SYSTEMS = ["schema_only", "schema_true_joins", "baseline_rules"]

SYSTEM_RUNNERS = {
    "baseline": b_runner.answer,
    "ktx": ktx_run.answer,
    "datus": datus_run.answer,
    "wren": wren_run.answer,
    "schema_only": controls.answer_schema_only,
    "schema_true_joins": controls.answer_schema_true_joins,
    "baseline_rules": controls.answer_baseline_rules,
}

def load_questions(db):
    path = os.path.join(ROOT, "questions", f"{db}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Validated question suite not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or []

def execute_gold(db, gold_sql):
    if not gold_sql:
        return None, None
    try:
        cols, rows = b_runner.run_sql(db, gold_sql)
        return rows, None
    except Exception as e:
        return None, f"Gold SQL execution failed: {str(e)[:200]}"

def run_evaluation(systems, dbs, runs=1, only=None, output_csv=None):
    os.makedirs(os.path.join(ROOT, "results", "raw"), exist_ok=True)
    if not output_csv:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = os.path.join(ROOT, "results", "raw", f"suite_results_{ts}.csv")

    csv_fields = [
        "system",
        "run_num",
        "db",
        "question_id",
        "category",
        "passed",
        "seconds",
        "tokens_in",
        "tokens_out",
        "sql",
        "error",
        "candidate_rows_count",
        "gold_rows_count",
    ]

    gold_cache = {}
    rows_logged = []

    print(f"\n=======================================================")
    print(f"STARTING DBEVAL SUITE RUN")
    print(f"Systems : {', '.join(systems)}")
    print(f"Databases: {', '.join(dbs)}")
    print(f"Runs    : {runs}")
    if only:
        print(f"Filtering on {len(only)} questions: {', '.join(sorted(only))}")
    print(f"Output  : {output_csv}")
    print(f"=======================================================\n")

    with open(output_csv, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=csv_fields)
        writer.writeheader()

        for run_idx in range(1, runs + 1):
            print(f"\n>>> BEGINNING RUN {run_idx} OF {runs} <<<")

            for db in dbs:
                questions = load_questions(db)
                if only:
                    questions = [q for q in questions if q["id"] in only]

                for q in questions:
                    q_id = q["id"]
                    category = q.get("category", "unknown")
                    question_text = q["question"]
                    gold_sql = q.get("gold_sql")
                    ordered = bool(q.get("ordered", False))

                    if category == "ambiguous" or not gold_sql:
                        print(f"[{db.upper()} | {q_id}] Ambiguous question, skipping automated scoring.")
                        continue

                    # Cache gold execution so we don't re-run gold SQL unnecessarily
                    if (db, q_id) not in gold_cache:
                        gold_rows, gold_err = execute_gold(db, gold_sql)
                        gold_cache[(db, q_id)] = (gold_rows, gold_err)
                    else:
                        gold_rows, gold_err = gold_cache[(db, q_id)]

                    for sys_name in systems:
                        runner_fn = SYSTEM_RUNNERS[sys_name]
                        ans = runner_fn(db, question_text)

                        passed = False
                        error_msg = ans.get("error")

                        if gold_err:
                            error_msg = f"GOLD_ERR: {gold_err}"
                        elif error_msg:
                            passed = False
                        elif ans.get("rows") is not None and gold_rows is not None:
                            try:
                                passed = same(gold_rows, ans["rows"], ordered=ordered)
                            except Exception as cmp_err:
                                error_msg = f"CompareError: {str(cmp_err)[:100]}"
                                passed = False

                        record = {
                            "system": sys_name,
                            "run_num": run_idx,
                            "db": db,
                            "question_id": q_id,
                            "category": category,
                            "passed": passed,
                            "seconds": ans.get("seconds", 0.0),
                            "tokens_in": ans.get("tokens_in", 0),
                            "tokens_out": ans.get("tokens_out", 0),
                            "sql": ans.get("sql", ""),
                            "error": error_msg or "",
                            "candidate_rows_count": len(ans.get("rows") or []),
                            "gold_rows_count": len(gold_rows or []) if gold_rows is not None else 0,
                        }

                        writer.writerow(record)
                        f_out.flush()
                        rows_logged.append(record)

                        status_str = "PASS" if passed else "FAIL"
                        print(f"[{run_idx}/{runs}][{db}][{sys_name}][{q_id}]: {status_str} ({ans['seconds']}s, {ans['tokens_in']}+{ans['tokens_out']} tokens)")
                        if not passed and error_msg:
                            print(f"    Error: {error_msg}")

    print_summary(rows_logged, systems, dbs)
    print(f"\nSaved detailed evaluation log to: {output_csv}")
    return output_csv

def print_summary(records, systems, dbs):
    if not records:
        return
    print("\n" + "=" * 75)
    print("EVALUATION SUMMARY")
    print("=" * 75)
    header = f"{'System':<12} | {'DB':<8} | {'Passed':<12} | {'Accuracy':<10} | {'Avg Sec':<9} | {'Avg Tokens':<11}"
    print(header)
    print("-" * 75)

    for sys_name in systems:
        for db in dbs:
            subset = [r for r in records if r["system"] == sys_name and r["db"] == db]
            if not subset:
                continue
            passed_cnt = sum(1 for r in subset if r["passed"])
            total_cnt = len(subset)
            acc = passed_cnt / total_cnt if total_cnt > 0 else 0
            avg_sec = sum(r["seconds"] for r in subset) / total_cnt
            avg_tok = sum(r["tokens_in"] + r["tokens_out"] for r in subset) / total_cnt
            print(f"{sys_name:<12} | {db:<8} | {passed_cnt}/{total_cnt:<10} | {acc:>8.1%} | {avg_sec:>7.2f}s | {avg_tok:>10.0f}")
    print("=" * 75)

    run_nums = sorted({r["run_num"] for r in records})
    if len(run_nums) > 1:
        print("\nPER-RUN ACCURACY BREAKDOWN:")
        hdr_runs = " | ".join(f"{'Run ' + str(rn):<10}" for rn in run_nums)
        print(f"{'System':<12} | {'DB':<8} | {hdr_runs}")
        print("-" * (24 + 13 * len(run_nums)))
        for sys_name in systems:
            for db in dbs:
                cols = []
                for rn in run_nums:
                    sub = [r for r in records if r["system"] == sys_name and r["db"] == db and r["run_num"] == rn]
                    if sub:
                        p = sum(1 for r in sub if r["passed"])
                        cols.append(f"{p}/{len(sub)} ({p/len(sub):.0%})")
                    else:
                        cols.append("N/A")
                cols_str = " | ".join(f"{c:<10}" for c in cols)
                print(f"{sys_name:<12} | {db:<8} | {cols_str}")
        print("=" * 75)

def main():
    ap = argparse.ArgumentParser(description="dbeval comprehensive test suite runner")
    ap.add_argument(
        "--system",
        choices=["baseline", "ktx", "datus", "wren", "schema_only", "schema_true_joins", "baseline_rules", "controls", "all", "everything"],
        default="all",
        help="System to test: 'all' (baseline, ktx, datus, wren), 'controls' (schema_only, schema_true_joins, baseline_rules), 'everything' (all 7), or a specific system name"
    )
    ap.add_argument("--db", choices=["olist", "appdb", "both"], default="both")
    ap.add_argument("--runs", type=int, default=1, help="Number of repetitions across the full suite (default: 1)")
    ap.add_argument("--only", help="Comma-separated question IDs to run")
    ap.add_argument("--output", help="Custom output CSV path")
    args = ap.parse_args()

    if args.system == "all":
        systems = BENCHMARK_SYSTEMS
    elif args.system == "controls":
        systems = CONTROL_SYSTEMS
    elif args.system == "everything":
        systems = list(SYSTEM_RUNNERS.keys())
    else:
        systems = [args.system]

    dbs = ["olist", "appdb"] if args.db == "both" else [args.db]
    only = {x.strip() for x in args.only.split(",")} if args.only else None

    run_evaluation(systems=systems, dbs=dbs, runs=args.runs, only=only, output_csv=args.output)

if __name__ == "__main__":
    main()
