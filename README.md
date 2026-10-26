# dbeval

> Which data-agent context layer works best on *your* database? A neutral head-to-head evaluation over Postgres.

📖 **Final Evaluation Report:** Read the full findings, statistical tests, and failure analyses in [**`results/REPORT.md`**](results/REPORT.md).

---

### TL;DR

1. **Rules are the primary lever:** Encoding business rules lifts text-to-SQL accuracy from 12.5% to 87.5% on SaaS edge cases, but structuring them in semantic layer tools lands within 0 to 3 questions of pasting the rules directly into the prompt (`baseline_rules`).
2. **Tool structures show no statistical advantage:** At 50 questions across 3 repetitions (1,450 runs), all reviewed tools (ktx, Wren Engine, Datus) tie or sit slightly below raw prompt rules (all 95% bootstrap CIs span zero).
3. **Decision: PIVOT.** Future work shifts from benchmarking static semantic layer formats to **automated rule capture, induction, and verification** directly from databases and query logs.

### Head-to-Head Benchmark Results

All metrics reflect majority scoring across 3 repetitions per question evaluated with `codestral-2508` via Mistral AI.

| System | `appdb` (32 Qs) | `appdb` Acc | `olist` (18 Qs) | `olist` Acc | Net vs. `baseline_rules` |
|---|:---:|:---:|:---:|:---:|:---:|
| **`baseline`** (raw schema + samples) | 4.0 / 32 | 12.5% | 13.0 / 18 | 72.2% | -24.0 Qs ($p < 0.001$) |
| **`baseline_rules`** (prompt rules) | **28.0 / 32** | **87.5%** | **15.0 / 18** | **83.3%** | — (reference) |
| **`wren_reviewed`** *(with engine rewrite)* | **28.0 / 32** | **87.5%** | 14.0 / 18 | 77.8% | +0.0 Qs ($p = 1.000$) |
| **`ktx_reviewed`** *(YAML metrics & desc)* | 26.33 / 32 | 82.3% | 15.0 / 18 | 83.3% | -1.67 Qs ($p = 0.375$) |
| **`datus_reviewed`** *(with free-text drop-in)* | 26.33 / 32 | 82.3% | **16.33 / 18** | **90.7%** | -1.67 Qs ($p = 0.688$) |
| **`datus_reviewed_defonly`** *(DDL comments only)* | 25.33 / 32 | 79.2% | 14.67 / 18 | 81.5% | -2.67 Qs ($p = 0.289$) |

---

### Upstream Open-Source Contributions & Fixes

During benchmark execution and engine audits, `dbeval` surfaced and resolved two fundamental failure modes in upstream repositories:

1. **[`kaelio/ktx#377`](https://github.com/kaelio/ktx/issues/377)** — *Silent Enrichment Failure & Cache Poisoning*:
   When external LLM enrichment failed (e.g. gateway 404 or rate limits), `@kaelio/ktx` silently reported exit code 0, cached empty/null results, and bypassed per-table resume. Fixed with total failure detection, truthful exit status reporting, and safe resume handling.
2. **[`Datus-ai/Datus-agent#1542`](https://github.com/Datus-ai/Datus-agent/issues/1542)** — *Foreign Key Omission in Reconstructed Table DDL*:
   `datus-postgresql` reconstructed table DDL by restricting constraints to `contype IN ('p', 'u')`, omitting all foreign keys and forcing LLMs to guess join keys. Patched in `datus-db-adapters` with deterministic constraint ordering and unvalidated (`NOT VALID`) foreign key separation.

---

## Overview

A fair, neutral benchmark comparing four ways of letting an LLM answer database questions over Postgres:
1. **Plain LLM Baseline** (Schema + 3 sample values per column)
2. **ktx** (`@kaelio/ktx@0.16.0`)
3. **Datus (stored context)** (`datus-agent 0.4.3` + `datus-postgresql 0.1.9`)
4. **Wren Engine** (`wren-engine 0.6.0`)

Evaluated over two distinct databases:
- **Olist:** Real-world Brazilian e-commerce dataset (tables without foreign keys).
- **appdb:** Realistic synthetic SaaS database with edge cases (test accounts, soft deletes, multi-currency cents, cancels vs churn).

---

## How Each Tool Is Run

To maintain strict neutrality, all four systems are evaluated against the identical fixed answering model (**`codestral-2508`** via Mistral AI) with read-only database credentials (`reader`). Each tool's generated layer provides its specialized semantic context.

| System | Tool Version | Layer Artifact Location | Layer Contents | Execution Modality |
|---|---|---|---|---|
| **Baseline** | Native Python | Direct DB introspection | Tables, columns, PKs, 3 sample values / col | Raw schema + samples in prompt |
| **ktx** | `@kaelio/ktx@0.16.0` | `layers/ktx/<db>/semantic-layer/` | Table schemas + Inferred foreign keys (YAML) | Schema + Inferred joins in prompt |
| **Datus (stored context)** | `datus-agent 0.4.3` | `layers/datus/<db>/` (`schema_metadata.json`, `schema_value.json`) | LanceDB table DDL, PKs, sample rows | RAG-retrieved definitions & samples in prompt (+ native agent reported separately) |
| **Wren Engine** | `wren-engine 0.6.0` | `layers/wren/<db>/target/mdl.json` | MDL compiled models, columns, declared relationships | Compiled MDL schemas & relationships in prompt |

### 1. Plain LLM Baseline (`runners/baseline.py`)
- **Introspection:** Queries PostgreSQL `information_schema` and `pg_catalog` via SQLAlchemy to extract column names, data types, nullability, and primary keys.
- **Sampling:** Fetches 3 sample values per column directly from the database.
- **Prompt:** Feeds raw table DDL and sample values to `codestral-2508` with zero semantic guidance, relationship hints, or business logic.
- **Execution:** Generates raw SQL and executes it with a 15-second statement timeout and 500-row limit.

### 2. ktx (`runners/ktx_run.py`)
- **Inferred Joins:** ktx automatically infers relationships between tables using naming heuristics and distinct value matching. In our benchmark, ktx scored **100% precision** (zero false positives) across both databases:
  - **Olist:** 6 unique inferred joins (85.7% undeclared recall).
  - **appdb:** 7 unique inferred joins (100% declared FK recall, 80.0% undeclared recall, discovering 4 of 5 undeclared SaaS relationships).
- **Enrichment Caveat:** ktx description enrichment was not evaluated because its `@ai-sdk/gateway` backend requires the Vercel AI Gateway protocol (which returns HTTP 404 on Mistral's OpenAI-compatible endpoint). Join inference was evaluated.
- **Runner:** `runners/ktx_run.py` reads the semantic layer YAML from `layers/ktx/<db>/semantic-layer/` and formats the inferred join paths (`table1.colA = table2.colB`) alongside table definitions into the prompt.

### 3. Datus (stored context) (`runners/datus_run.py`)
- **Architecture & LanceDB Persistence:** Datus crawls the database and builds local LanceDB vector tables (`schema_metadata.lance` and `schema_value.lance`) using local ONNX embeddings (`all-MiniLM-L6-v2-onnx`). These tables are exported into `layers/datus/<db>/` as JSON and Parquet for full inspectability.
- **Connector Finding:** Inspection of `datus_postgresql/connector.py` reveals that Datus extracts column metadata and `PRIMARY KEY ("id")`, but does not query or extract `FOREIGN KEY` constraints.
- **Runner Modalities:**
  1. **Standard Context Layer:** `runners/datus_run.py` retrieves relevant table definitions and sample rows from the exported metadata to augment `codestral-2508`.
  2. **End-to-End Agent Benchmark:** Datus's built-in `PrintModeRunner` autonomous text-to-SQL agent is run and reported separately for comparative analysis.

### 4. Wren Engine (`runners/wren_run.py`)
- **Engine vs. Product:** We test `wren-engine 0.6.0` (the open-source core Python compiler and semantic engine), not the multi-container Docker Wren AI platform.
- **Layer Compilation:** Models and relationships are defined in Modeling Definition Language (MDL) and compiled into `target/mdl.json`.
- **Introspection Finding:** Wren Engine is a deterministic semantic compiler. In `appdb_v2`, introspected foreign keys were compiled into 3 declared relationships (`invoices -> accounts`, `subscriptions -> accounts`, `invoices -> subscriptions`). On Olist, zero relationships are declared.
- **Runner:** `runners/wren_run.py` parses `target/mdl.json`, extracts defined relationships and column types, and supplies the compiled semantic models to `codestral-2508`.

---

## Question Suite (`suite-v1`)

The benchmark evaluates **53 total questions** across both databases:
- **`appdb` (34 questions):** 7 simple lookups, 15 business metrics (revenue, churn, ARPA, MRR, login activity), 10 multi-join queries, and 2 ambiguous questions. All 34 questions validated with 100% agreement between hand-written SQL and independent oracles.
- **`olist` (19 validated questions + 3 disputed findings):** 4 simple lookups, 7 metric questions, 7 multi-join queries, and 1 ambiguous question.

---

## Model Selection & Rate Limits

All systems under test run against the exact same LLM:
- **Evaluation Model:** `codestral-2508` via Mistral AI (`https://api.mistral.ai/v1`)
- **Throughput & Limits:** 625,000 tokens/min and 2.08 requests/sec on Mistral's Experiment plan (free tier).
- **Rate Pacing:** 1.1s inter-request pause with automatic exponential backoff retry on HTTP 429.
- **Independent Validation Oracles:** `openai/gpt-oss-120b` and `qwen/qwen3.8-27b` via Groq.

---

## How to Reproduce

You can reproduce the evaluation locally. The answering model runs on Mistral AI's free experiment tier.

### 1. Environment Setup
```bash
git clone https://github.com/meet987654/dbeval.git
# Note for Windows: if hitting MAX_PATH limits, use: git clone -c core.longpaths=true <url>
cd dbeval
pip install -r requirements.txt
# Note: Python 3.11 or 3.12 is recommended. On Python 3.13+, run: pip install -U "sqlalchemy>=2.0.36"
cp .env.example .env
# Set your MISTRAL_API_KEY in .env
```

### 2. Start PostgreSQL Databases via Docker
Launch the PostgreSQL 16 container hosting `appdb` and `olist` (port 5433):
```bash
docker compose up -d
```
*(If seeding the databases from scratch, run `python db/seed_appdb.py` to generate synthetic SaaS data. Close other connections to `appdb` before re-running the seed script, as dropping tables requires an exclusive lock. Loading the raw Brazilian e-commerce dataset via `python db/load_olist.py` downloads from Kaggle and requires a Kaggle account configured with `kaggle.json` or environment credentials).*

### 3. Verify Comparator & Run Benchmark Suites
```bash
# Verify the comparison engine:
python scorer/test_compare.py

# Smoke test on 3 questions:
python scorer/run_suite.py --system baseline --db appdb --only appdb-001,appdb-002,appdb-003

# Run 3 repetitions of all systems on both databases:
python scorer/run_suite.py --system everything --db both --runs 3
```

### 4. Run Paired Statistical Analysis
Compute exact sign-test p-values, 95% bootstrap confidence intervals, and failure classifications:
```bash
# Analysis vs plain LLM baseline:
python scorer/analyze.py results/raw/suite_results_all.csv --baseline baseline --ties half --out results/ANALYSIS_REVIEWED.md

# Analysis vs prompt rules (baseline_rules):
python scorer/analyze.py results/raw/suite_results_all.csv --baseline baseline_rules --ties half --out results/ANALYSIS_VS_RULES.md

# Categorize failure attributions:
python scorer/label_failures.py results/raw/suite_results_all.csv --out results/FAILURES_REVIEWED.md
```

---

## Development Milestones & Status Log

- [x] **Day 1: Baseline & Second Database:** Seeded `appdb` with real-world SaaS edge cases (test accounts, soft deletes, multi-currency cents, cancels vs. churn). Built `runners/baseline.py`.
- [x] **Day 2: Business Rules & Question Suites:** Defined answer-key rules in `docs/business_rules.md`. Created dual-oracle validation harness (`scorer/validate_gold.py`) with Groq models.
- [x] **Day 3: Out-of-the-Box Layer Generation:** Built and audited semantic layers for ktx, Datus, and Wren Engine across both databases. Benchmarked ktx inferred join quality (100% precision). Rebuilt `appdb_v2` after `REFERENCES` grant. Exported Datus LanceDB metadata to JSON and Parquet.
- [x] **Question Suite Frozen (`suite-v1`):** 53 validated questions (34 `appdb`, 19 `olist`, consisting of 50 scored and 3 ambiguous). Tagged `suite-v1`.
- [x] **Day 4: Test Harness & 3x Full Evaluation:** Built runners and `scorer/run_suite.py`. Completed 3 full evaluation passes (600 queries) with `codestral-2508` across all 4 systems on both databases. Context layers improved Olist accuracy by ~9.3 percentage points over baseline while cutting prompt tokens by up to 75%. Raw logs saved in `results/raw/suite_results_20261021_184203.csv`.
- [x] **Day 5: Timed Review, Execution Fixes & Final Report:** Encoded business rules across ktx, Wren Engine, and Datus. Fixed Wren engine SQL rewriting pass to resolve calculated fields. Isolated the Datus free-text drop-in effect. Completed 3 repetitions (1,450 total runs) and generated paired statistical reports (`scorer/analyze.py`) and failure attribution (`scorer/label_failures.py`). Tagged `study-v1` and `study-v1.3`.

### Pre-Registered Decision Rule
At the end of Week 0, the project evaluated the pre-registered criteria in `docs/DAY5_PROTOCOL.md`:
- **Outcome: Pivot to Rule Induction & Verification.** Reviewed tools all landed near `baseline_rules` (Wren 28.0/32 matching baseline_rules 28.0/32, ktx 26.33/32, Datus 25.33–26.33/32). Rules are the lever. Future efforts focus on discovering and verifying candidate rules directly from production databases and query logs.

---

## License

This project is licensed under the [MIT License](LICENSE).
