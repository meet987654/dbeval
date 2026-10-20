# dbeval

> Which data-agent context layer works best on *your* database? A neutral head-to-head, starting with Postgres.

## Status

**Current Status:** Day 2 Complete (Business rules defined, gold question suites created, comparison scorer tested, dual-oracle validation executed). Ready for Day 3 (Build each tool's layer). Follow along in [docs/WEEK0_GUIDE.md](docs/WEEK0_GUIDE.md).

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
2. **ktx**
3. **Datus**
4. **Wren**

Evaluated over two distinct databases:
- **Olist:** Real-world Brazilian e-commerce dataset (tables without foreign keys).
- **appdb:** Realistic synthetic SaaS database with edge cases (test accounts, soft deletes, multi-currency cents, cancels vs churn).

See [docs/WEEK0_GUIDE.md](docs/WEEK0_GUIDE.md) for full instructions and daily schedule.

---

## Model Selection & Rate Limits

All four systems under test run on the exact same model:
- **Evaluation Model:** `codestral-2508` via Mistral AI (`https://api.mistral.ai/v1`)
- **Throughput & Limits:** 625,000 tokens/min and 2.08 requests/sec on Mistral's Experiment plan. Runner includes a 1.1s inter-request pause and automatic 429 backoff retry.
- **Model Selection Rationale:**
  - `mistral-large-2512` and `mistral-large-latest` returned `403 tier_not_allowed` on the free tier.
  - `mistral-small-2603`, `mistral-medium-latest`, and `mistral-large-4` were excluded due to a restrictive 20,000 tokens/min limit (~5 calls/min).
  - `codestral-2508` is a pinned, dated model specifically built for code/SQL generation with high throughput.
- **Gold Answer Oracles:** Validated with independent Groq models (`openai/gpt-oss-120b` and `qwen/qwen3.8-27b`) to prevent self-evaluating bias.

---

## Evaluation Architecture Design Decision

- **Fixed Answering Agent:** All tools are evaluated using a fixed answering agent powered by `codestral-2508` via Mistral AI, with each tool supplying its context layer as prompt augmentation.
- **End-to-End Capabilities:** Tools that feature native execution pipelines (such as Datus's `PrintModeRunner` or Wren Engine's compiler/connector) also have their end-to-end performance logged and reported separately for comparison against the unified answering agent.
- **Isolation:** Read-only PostgreSQL access via the dedicated `reader` user (`postgresql://reader:reader@localhost:5433/<db>`).


