"""Question-level analysis of dbeval results (paired, honest about small samples).

Run:
    python scorer/analyze.py results/raw/suite_results_XXXX.csv
    python scorer/analyze.py results/raw/suite_results_XXXX.csv --baseline baseline --markdown-out results/ANALYSIS.md
    python scorer/analyze.py results/raw/suite_results_XXXX.csv --ties half --matrix results/per_question.csv

Why this exists: the 3 repeated runs are nearly identical at temperature 0, so counting them as
54 or 96 independent trials overstates the evidence. The real sample size is the number of
QUESTIONS (18 olist, 32 appdb). This script therefore:
  1. scores each question by majority over the runs,
  2. compares every system to the baseline question by question (who fixed it, who broke it),
  3. gives an exact sign-test p-value and a bootstrap 95% interval over questions,
  4. writes a per-question matrix so you can read the actual differences.

Column names are auto-detected. If detection fails, pass --col-system, --col-db, --col-question,
--col-run, --col-passed explicitly.
"""

import argparse
import csv
import math
import os
import random
from collections import defaultdict

CANDIDATES = {
    "system": ["system"],
    "db": ["db", "database"],
    "question": ["question_id", "question", "qid", "id"],
    "run": ["run", "run_num", "run_id", "iteration", "pass_num", "repeat"],
    "passed": ["passed", "correct", "is_correct", "success", "match", "ok", "pass"],
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
    raise SystemExit(f"Could not find a '{key}' column. Headers are: {headers}\n"
                     f"Pass --col-{key} <name>.")


def to_bool(v):
    s = str(v).strip().lower()
    if s in TRUE:
        return True
    if s in FALSE:
        return False
    raise ValueError(f"cannot read pass/fail from {v!r}")


def sign_test_p(b, c):
    """Exact two-sided sign test on discordant pairs b (tool right, baseline wrong), c (reverse)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap_diff(tool, base, reps=5000, seed=1):
    rng = random.Random(seed)
    n = len(tool)
    diffs = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        diffs.append(sum(tool[i] - base[i] for i in idx) / n * 100)
    diffs.sort()
    return diffs[int(0.025 * reps)], diffs[int(0.975 * reps)]


def run_analysis(
    csv_path,
    baseline="baseline",
    out=None,
    matrix="results/per_question.csv",
    ties="fail",
    col_overrides=None,
    quiet=False,
):
    """Run question-level analysis, generate markdown tables, and write output files."""
    col_overrides = col_overrides or {}
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Empty results CSV: {csv_path}")

    headers = list(rows[0].keys())
    col = {k: detect(headers, k, col_overrides.get(k)) for k in CANDIDATES}
    infra_col = next((h for h in headers if h.lower() == "infra_error"), None)
    cat_col = next((h for h in headers if h.lower() == "category"), None)

    dropped_infra = 0
    runs = defaultdict(list)  # (db, system, question) -> [bool, ...]
    for r in rows:
        if cat_col and r[cat_col] == "ambiguous":
            continue
        if infra_col and str(r[infra_col]).strip().lower() in TRUE:
            dropped_infra += 1
            continue
        runs[(r[col["db"]], r[col["system"]], r[col["question"]])].append(to_bool(r[col["passed"]]))

    dbs = sorted({k[0] for k in runs})
    systems = sorted({k[1] for k in runs})
    if baseline not in systems:
        raise SystemExit(f"Baseline system {baseline!r} not found. Systems: {systems}")

    # majority per question (ties count as pass only if strictly more than half)
    def majority(vals):
        return sum(vals) * 2 > len(vals)

    def score(vals):
        if ties == "half":
            return sum(vals) / len(vals) if vals else 0.0
        return 1.0 if majority(vals) else 0.0

    out_lines = []
    out_lines.append("# dbeval analysis (question-level)\n")
    out_lines.append(f"Source: `{csv_path}`. Rows dropped for infrastructure errors: {dropped_infra}.\n")
    matrix_dict = defaultdict(dict)

    for db in dbs:
        qs = sorted({k[2] for k in runs if k[0] == db})
        present = [s for s in systems if any(k[0] == db and k[1] == s for k in runs)]
        if baseline not in present:
            continue
        per = {s: [] for s in present}
        flaky = {s: 0 for s in present}
        for s in present:
            for q in qs:
                vals = runs.get((db, s, q), [])
                per[s].append(score(vals))
                if vals and 0 < sum(vals) < len(vals):
                    flaky[s] += 1
                matrix_dict[(db, q)][s] = f"{sum(vals)}/{len(vals)}" if vals else "-"
        n = len(qs)
        out_lines.append(f"\n## {db}  ({n} questions)\n")
        out_lines.append("| system | questions passed | accuracy | flaky questions* |")
        out_lines.append("|---|---|---|---|")
        for s in present:
            out_lines.append(f"| {s} | {sum(per[s]):g}/{n} | {sum(per[s]) / n * 100:.1f}% | {flaky[s]} |")
        out_lines.append("\n*flaky = passed in some runs but not all.\n")
        how = "pass rate across runs" if ties == "half" else "pass if it passed in most runs"
        out_lines.append(f"\nPaired comparison against `{baseline}` (question score: {how}):\n")
        out_lines.append("| system | fixed (tool right, baseline wrong) | broke (baseline right, tool wrong) | net questions | diff (points) | 95% bootstrap interval | sign-test p |")
        out_lines.append("|---|---|---|---|---|---|---|")
        base = per[baseline]
        for s in present:
            if s == baseline:
                continue
            fixed = sum(1 for t, bse in zip(per[s], base) if t > bse)
            broke = sum(1 for t, bse in zip(per[s], base) if t < bse)
            lo, hi = bootstrap_diff(per[s], base)
            net = sum(per[s]) - sum(base)
            diff = net / n * 100
            out_lines.append(f"| {s} | {fixed} | {broke} | {net:+g} | {diff:+.1f} | [{lo:+.1f}, {hi:+.1f}] | {sign_test_p(fixed, broke):.3f} |")
        out_lines.append(f"\nOne question is worth {100 / n:.1f} points on this database. "
                         "An interval that includes 0, or p above 0.05, means the difference is not distinguishable from noise.\n")

    text = "\n".join(out_lines)
    if not quiet:
        print(text)

    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        if not quiet:
            print(f"\nWrote markdown report to {out}")

    if matrix:
        os.makedirs(os.path.dirname(matrix) or ".", exist_ok=True)
        with open(matrix, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["db", "question"] + systems)
            for (db, q), d in sorted(matrix_dict.items()):
                w.writerow([db, q] + [d.get(s, "-") for s in systems])
        if not quiet:
            print(f"Wrote per-question matrix to {matrix}")

    return text, matrix_dict


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path", help="Path to raw suite results CSV")
    ap.add_argument("--baseline", default="baseline", help="Baseline system name to compare against")
    ap.add_argument("--markdown-out", "--out", dest="out", default=None,
                    help="Path to write formatted Markdown report tables")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="Suppress printing formatted Markdown report to stdout")
    for k in CANDIDATES:
        ap.add_argument(f"--col-{k}", help=f"Explicit column name for '{k}'")
    ap.add_argument("--matrix", default="results/per_question.csv",
                    help="Path to export per-question CSV matrix (default: results/per_question.csv)")
    ap.add_argument("--ties", choices=["fail", "half"], default="fail",
                    help="how to score a question that passed in only some runs: 'fail' = majority vote "
                         "(a 1-of-2 split counts as a fail), 'half' = use the pass rate (1 of 2 = 0.5). "
                         "Use 'half' when you have only 2 runs.")
    args = ap.parse_args(argv)

    col_overrides = {k: getattr(args, f"col_{k}") for k in CANDIDATES if getattr(args, f"col_{k}")}
    run_analysis(
        csv_path=args.csv_path,
        baseline=args.baseline,
        out=args.out,
        matrix=args.matrix,
        ties=args.ties,
        col_overrides=col_overrides,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
