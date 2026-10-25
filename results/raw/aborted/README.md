# Aborted / Partial Benchmark Runs

This directory preserves or documents aborted, interrupted, or partial evaluation runs.

### `suite_results_20261023_112555.csv` (1,479 bytes)
- **Timestamp:** 2026-10-23 11:25:55 UTC (step index 3327)
- **Status:** Aborted after 4 questions of pass 1 on Olist.
- **Reason:** Docker Desktop daemon was not yet running; the process threw a PostgreSQL connection failure when `schema_only` attempted live introspections against port 5433.
- **Resolution:** Docker daemon was started via Docker Desktop, containers verified healthy with `docker compose up -d`, and the full 2-pass suite was re-run cleanly as `results/raw/suite_results_20261023_115601.csv`.

### `suite_results_20261026_000707.csv`
- **Timestamp:** 2026-10-26 00:07:07
- **Status:** Single-question smoke check (`appdb-001`, 1 run).
- **Reason:** Clean-clone / fresh virtual environment reproduction verification.
