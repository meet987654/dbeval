# dbeval

> Which data-agent context layer works best on *your* database? A neutral head-to-head, starting with Postgres.

## Status

- [x] **Day 1: Baseline & Second Database:** Seeded `appdb` with real-world SaaS edge cases (test accounts, soft deletes, multi-currency cents, cancels vs. churn). Built `runners/baseline.py`.
- [x] **Day 2: Business Rules & Question Suites:** Defined answer-key rules in `docs/business_rules.md`. Created dual-oracle validation harness (`scorer/validate_gold.py`) with Groq models.
- [x] **Day 3: Out-of-the-Box Layer Generation:** Built and audited semantic layers for ktx, Datus, and Wren Engine across both databases. Benchmarked ktx inferred join quality (100% precision). Rebuilt `appdb_v2` after `REFERENCES` grant. Exported Datus LanceDB metadata to JSON and Parquet.
- [x] **Question Suite Frozen (`suite-v1`):** 53 validated questions (34 `appdb`, 19 `olist`, consisting of 50 scored and 3 ambiguous). Tagged `suite-v1`.
- [ ] **Day 4: Test Harness & 3x Full Evaluation:** Implementing `runners/*` and `scorer/run_suite.py` to run 3 full evaluation passes with `codestral-2508`.

---

## The Decision Rule

At the end of Week 0, the project will move forward based on the following criteria:

- **Go:** Accuracy differs by more than about 10 points between tools on at least one database, or the ranking changes between databases.
- **Pivot:** One tool wins on everything. Then the idea shrinks to regression testing for a single layer, which is weaker.
- **Stop:** No tool beats the plain baseline by much. Then the idea that a layer helps is in doubt on your data. You still keep a solid portfolio project.

---

## Overview

A fair, neutral benchmark comparing four ways of letting an LLM answer database questions over Postgres:
1. **Plain LLM Baseline** (Schema + 3 sample values per column)
2. **ktx** (`@kaelio/ktx@0.16.0`)
3. **Datus** (`datus-agent 0.4.3` + `datus-postgresql 0.1.2`)
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
| **Datus** | `datus-agent 0.4.3` | `layers/datus/<db>/` (`schema_metadata.json`, `schema_value.json`) | LanceDB table DDL, PKs, sample rows | RAG-retrieved definitions & samples in prompt (+ native agent reported separately) |
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

### 3. Datus (`runners/datus_run.py`)
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
- **Throughput & Limits:** 625,000 tokens/min and 2.08 requests/sec on Mistral's Experiment plan.
- **Rate Pacing:** 1.1s inter-request pause with automatic exponential backoff retry on HTTP 429.
- **Independent Validation Oracles:** `openai/gpt-oss-120b` and `qwen/qwen3.8-27b` via Groq.
