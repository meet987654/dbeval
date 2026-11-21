# Results index

Where to find each output of the dbeval study. Start with `REPORT.md`.

## Summary
- `REPORT.md` / `REPORT.html`: the final evaluation report.
- `benchmark_dashboard.html`: interactive dashboard of the scores.
- `DATUS_BREAKDOWN.md`: per-question breakdown of Datus, written for the Datus team.

## Question-level analysis
Each file lists, per system, questions passed, accuracy and flaky questions. The source CSV is named at the top of each file.
- `ANALYSIS.md`: first suite run (`raw/suite_results_20261023_115601.csv`).
- `ANALYSIS_CONTROLS.md`: runs that include the control systems (`raw/suite_results_with_controls.csv`).
- `ANALYSIS_REVIEWED.md`: all systems including the reviewed layers (`raw/suite_results_all.csv`).
- `ANALYSIS_VS_RULES.md`: same data as above, compared against `baseline_rules` (`raw/suite_results_all.csv`).

## Failure attribution
Failures categorised by comparing candidate SQL to the gold SQL and Postgres errors.
- `FAILURES.md`: for the first suite run.
- `FAILURES_REVIEWED.md`: for the run with reviewed layers.
- `failure_labels.csv`: the labels in machine-readable form.

## Raw data
- `per_question.csv`, `per_question_with_controls.csv`: per-question results.
- `raw/`: one CSV per suite run, plus `suite_results_all.csv` (combined) and `suite_results_datus_defonly.csv`.
- `datus_smoke_results.json`, `wren_smoke_results.json`: smoke-test outputs.
