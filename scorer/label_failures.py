"""Failure attribution for dbeval benchmark results.

Inspects failed questions by comparing rule features in the system's generated SQL
against the gold SQL, detects SQL syntax/runtime errors, and assigns precise labels.

Counting: each (db, system, question_id) is counted ONCE -- the majority failure label
across all runs is used. Ties break alphabetically toward the stricter label.
This means totals equal the number of distinct failed questions, not run-rows.

Usage:
    python scorer/label_failures.py results/raw/suite_results_with_controls.csv --out results/FAILURES.md
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CANDIDATES = {
    "system": ["system"],
    "db": ["db", "database"],
    "question": ["question_id", "qid", "id"],
    "run": ["run", "run_num", "run_id", "iteration", "pass_num", "repeat"],
    "passed": ["passed", "correct", "is_correct", "success", "match", "ok", "pass"],
    "sql": ["sql", "candidate_sql", "query"],
    "error": ["error", "error_msg", "err"],
    "category": ["category"],
}

TRUE = {"1", "true", "t", "yes", "y", "pass", "passed"}
FALSE = {"0", "false", "f", "no", "n", "fail", "failed", ""}

def detect(headers, key, override):
    if override:
        return override
    lower = {h.lower(): h for h in headers}
    for c in CANDIDATES[key]:
        if c in lower:
            return lower[c]
    if key in ["error", "category", "sql", "run"]:
        return None
    raise SystemExit(f"Could not find a '{key}' column. Headers: {headers}")

def load_gold_questions():
    golds = {}
    for db in ["appdb", "olist"]:
        path = os.path.join(ROOT, "questions", f"{db}.yaml")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
                for q in data:
                    golds[(db, q["id"])] = q
    return golds

def classify_sql_error(err_msg):
    if not err_msg:
        return None
    err = str(err_msg).lower()
    if "groupingerror" in err or "aggregate" in err:
        return "sql_error:grouping_error"
    if "undefinedfunction" in err or "function round" in err or "does not exist" in err:
        return "sql_error:undefined_function"
    if "undefinedcolumn" in err or "column" in err and "does not exist" in err:
        return "sql_error:undefined_column"
    if "syntaxerror" in err or "syntax error" in err:
        return "sql_error:syntax_error"
    if "timeout" in err or "statement_timeout" in err:
        return "sql_error:timeout"
    if "refused:" in err:
        return "sql_error:non_select_refused"
    return "sql_error:runtime_error"

def extract_features_appdb(sql_text):
    if not sql_text:
        return set()
    s = sql_text.lower()
    features = set()
    if "is_test" in s:
        features.add("test_filter")
    if "deleted_at" in s:
        features.add("soft_delete")
    if "fx_rates" in s or "usd_per_unit" in s:
        features.add("fx_join")
    if "refunds" in s:
        features.add("refund_netting")
    if "/ 100" in s or "/100" in s or "* 0.01" in s or "*0.01" in s or "100.0" in s:
        features.add("cents_conversion")
    if "cancel_reason" in s:
        features.add("cancel_reason")
    if "status" in s and ("'active'" in s or '"active"' in s) and "subscriptions" in s:
        features.add("active_sub_filter")
    if "status" in s and ("'paid'" in s or '"paid"' in s):
        features.add("paid_invoice_filter")
    if "events" in s:
        features.add("user_events")
    if "plan_tier" in s:
        features.add("plan_tier")
    # Detect BETWEEN anti-pattern for date windows (should be half-open)
    if re.search(r"between\s+['\"]\d{4}-\d{2}-\d{2}", s):
        features.add("half_open_date")
    return features

def extract_features_olist(sql_text):
    if not sql_text:
        return set()
    s = sql_text.lower()
    features = set()
    if "customer_unique_id" in s:
        features.add("customer_unique_id")
    if "canceled" in s or "unavailable" in s:
        features.add("sales_status_filter")
    if "product_category_name_translation" in s or "translation" in s:
        features.add("category_translation")
    if "::timestamp" in s or "cast(" in s or "to_timestamp" in s or "::date" in s:
        features.add("date_cast")
    if "'delivered'" in s or '"delivered"' in s:
        features.add("delivered_filter")
    if "order_payments" in s and "order_items" not in s:
        features.add("payments_grain_isolated")
    return features

def label_failure(db, candidate_sql, gold_sql, err_msg):
    # 1. SQL runtime or syntax error
    sql_err = classify_sql_error(err_msg)
    if sql_err:
        return sql_err

    # 2. Compare features between gold and candidate
    if db == "appdb":
        gold_feats = extract_features_appdb(gold_sql)
        cand_feats = extract_features_appdb(candidate_sql)
    else:
        gold_feats = extract_features_olist(gold_sql)
        cand_feats = extract_features_olist(candidate_sql)

    missing = sorted(list(gold_feats - cand_feats))
    if missing:
        return f"missing:{'+'.join(missing)}"

    # 3. Check for specific anti-patterns
    cand_lower = (candidate_sql or "").lower()
    gold_lower = (gold_sql or "").lower()
    if db == "appdb":
        if "accounts.plan " in cand_lower or "a.plan " in cand_lower:
            return "wrong_column:used_plan_instead_of_plan_tier"
    if db == "olist":
        if "customer_id" in cand_lower and "customer_unique_id" in gold_lower and "customer_unique_id" not in cand_lower:
            return "missing:customer_unique_id"

    return "other"

def main():
    ap = argparse.ArgumentParser(description="Label and categorize failure modes for dbeval results")
    ap.add_argument("csv_path", help="Path to evaluation results CSV")
    ap.add_argument("--out", default="results/FAILURES.md", help="Markdown summary output path")
    ap.add_argument("--labels", default="results/failure_labels.csv", help="Detailed failure labels CSV output")
    for k in CANDIDATES:
        ap.add_argument(f"--col-{k}")
    args = ap.parse_args()

    golds = load_gold_questions()

    with open(args.csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"Empty results CSV: {args.csv_path}")

    headers = list(rows[0].keys())
    col = {k: detect(headers, k, getattr(args, f"col_{k}")) for k in CANDIDATES}

    # -------------------------------------------------------------------
    # First pass: collect all run-level results keyed by (db, sys, qid)
    # -------------------------------------------------------------------
    # key -> list of (passed, label, sql, err, row_dict)
    question_runs = defaultdict(list)

    for r in rows:
        passed_str = str(r[col["passed"]]).strip().lower()
        passed = passed_str in TRUE
        cat = r.get(col["category"]) if col["category"] else ""
        if cat == "ambiguous":
            continue

        db = r[col["db"]]
        sys_name = r[col["system"]]
        qid = r[col["question"]]
        sql = r.get(col["sql"], "") if col["sql"] else ""
        err = r.get(col["error"], "") if col["error"] else ""
        gold_q = golds.get((db, qid), {})
        gold_sql = gold_q.get("gold_sql", "")

        if passed:
            lbl = "PASS"
        else:
            lbl = label_failure(db, sql, gold_sql, err)

        question_runs[(db, sys_name, qid)].append((passed, lbl, sql, err, r, gold_sql))

    # -------------------------------------------------------------------
    # Second pass: pick per-question label (majority vote across runs)
    # -------------------------------------------------------------------
    labeled_rows = []
    failure_counts = defaultdict(lambda: defaultdict(int))  # (db, system) -> label -> count
    total_failures = defaultdict(int)  # (db, system) -> int

    for (db, sys_name, qid), run_list in question_runs.items():
        labels_this_q = [lbl for (_p, lbl, _s, _e, _r, _g) in run_list]
        # Majority label; any run passing => count as PASS for that question
        pass_count = sum(1 for lbl in labels_this_q if lbl == "PASS")
        if pass_count > len(labels_this_q) / 2:
            chosen_label = "PASS"
        else:
            # Most common failure label; ties: alphabetical
            from collections import Counter
            cnt = Counter(lbl for lbl in labels_this_q if lbl != "PASS")
            chosen_label = min(cnt, key=lambda l: (-cnt[l], l))

        # Use the last run's row as representative
        _, _, best_sql, best_err, best_row, gold_sql = run_list[-1]

        if chosen_label != "PASS":
            failure_counts[(db, sys_name)][chosen_label] += 1
            total_failures[(db, sys_name)] += 1

        rec = dict(best_row)
        rec["failure_label"] = chosen_label
        rec["gold_sql"] = gold_sql
        labeled_rows.append(rec)

    # Write failure_labels.csv
    os.makedirs(os.path.dirname(args.labels) or ".", exist_ok=True)
    out_headers = list(rows[0].keys()) + ["failure_label", "gold_sql"]
    with open(args.labels, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_headers)
        writer.writeheader()
        writer.writerows(labeled_rows)
    print(f"Wrote detailed failure labels to: {args.labels}")

    # Build Markdown report
    md = []
    md.append("# dbeval Failure Attribution Report\n")
    md.append(f"Source: `{args.csv_path}`\n")
    md.append("Failures are categorized by automated comparison of candidate SQL against the gold SQL rule requirements and PostgreSQL engine errors.\n")

    dbs = sorted({k[0] for k in failure_counts})
    systems = sorted({k[1] for k in failure_counts})

    for db in dbs:
        md.append(f"\n## Database: {db}\n")
        db_systems = [s for s in systems if (db, s) in total_failures]

        # Top labels for this db
        all_labels_db = sorted({lbl for s in db_systems for lbl in failure_counts[(db, s)]})

        md.append(f"| Failure Label | " + " | ".join(db_systems) + " |")
        md.append("|---|" + "|".join([":---:"] * len(db_systems)) + "|")
        for lbl in all_labels_db:
            counts = [str(failure_counts[(db, s)].get(lbl, 0)) for s in db_systems]
            md.append(f"| `{lbl}` | " + " | ".join(counts) + " |")

        totals = [str(total_failures[(db, s)]) for s in db_systems]
        md.append(f"| **TOTAL FAILURES** | " + " | ".join(totals) + " |\n")

    # Deep dive into other and baseline_rules failures on appdb
    md.append("\n## Detailed Inspection: `other` and `baseline_rules` Failures\n")
    md.append("Below are questions where `failure_label` is `other` or where `baseline_rules` failed:\n\n")

    seen_inspect = set()
    for r in sorted(labeled_rows, key=lambda x: (x[col["db"]], x[col["question"]], x[col["system"]])):
        if r["failure_label"] == "PASS":
            continue
        db = r[col["db"]]
        qid = r[col["question"]]
        sys_name = r[col["system"]]
        lbl = r["failure_label"]

        if lbl == "other" or (sys_name == "baseline_rules" and db == "appdb"):
            key = (db, qid, sys_name)  # deduplicate per question, not per label
            if key in seen_inspect:
                continue
            seen_inspect.add(key)
            gold_q = golds.get((db, qid), {})
            q_text = gold_q.get("question", "")
            md.append(f"### [{db}] {qid} ({sys_name}) - Label: `{lbl}`\n")
            md.append(f"**Question:** {q_text}\n\n")
            if r.get(col["error"]):
                md.append(f"**Error:** `{r.get(col['error'])[:200]}`\n\n")
            md.append("```sql\n-- Candidate SQL:\n" + (r.get(col["sql"]) or "").strip() + "\n```\n")
            md.append("```sql\n-- Gold SQL:\n" + (r.get("gold_sql") or "").strip() + "\n```\n\n")

    md_text = "\n".join(md)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md_text)
        print(f"Wrote failure analysis report to: {args.out}")

    print("\nSummary of Failures:")
    for db in dbs:
        print(f"\n--- {db.upper()} ---")
        for s in systems:
            if (db, s) in total_failures:
                print(f"  {s:<18}: {total_failures[(db, s)]} failures")
                for lbl, cnt in sorted(failure_counts[(db, s)].items(), key=lambda x: -x[1])[:5]:
                    print(f"     - {lbl}: {cnt}")

if __name__ == "__main__":
    main()
