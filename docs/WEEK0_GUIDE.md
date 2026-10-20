# dbeval: Week 0 Guide

Put this file in the repo as `docs/WEEK0_GUIDE.md` and tick things off as you go.

## What you are doing this week

You are running a fair race between four ways of letting an AI answer questions about a database:

1. A plain LLM that only sees the table definitions (the baseline)
2. ktx
3. Datus
4. Wren

You run the same questions on the same databases with the same model. Then you count who got the answer right.

At the end of the week you will know two things:

- Do the tools score differently enough that a neutral comparison is useful?
- Does the ranking change from one database to another?

Customer calls and outreach are **not** part of this guide. They come later.

```mermaid
flowchart LR
  A[Two Postgres databases] --> B[Validated questions]
  B --> C[Four runners]
  C --> D[Scorer]
  D --> E[Results CSV]
  E --> F[REPORT.md and decision]
```

---

## 1. What the repo should have (and nothing more)

```
dbeval/
  README.md              pitch, status, decision rule
  .gitignore             data/, .env, __pycache__/
  .env.example           DB urls, LLM_MODEL, API keys (names only)
  docker-compose.yml     local Postgres
  docs/
    WEEK0_GUIDE.md       this file
  db/
    init.sql             creates databases and the read-only role
    load_olist.py        loads the Olist CSVs
    seed_appdb.py        builds the fake SaaS database
  data/                  raw CSVs (gitignored)
  questions/
    olist.yaml           validated questions
    appdb.yaml
    disputed/            questions where gold answers disagreed
  runners/
    baseline.py          the plain-LLM runner
    ktx_run.py           added on day 4
    datus_run.py         added on day 4
    wren_run.py          added on day 4
  scorer/
    compare.py           compares two result sets
    run_suite.py         runs every question, writes the CSV
  notes/
    ktx.md               setup log: time taken, steps, problems
    datus.md
    wren.md
  results/
    raw/                 one CSV per run
    REPORT.md            the write-up (day 7)
```

**Do not add yet:** a web UI, a GitHub Action, a pip package, a hosted version, or other databases. Those only matter if the week-0 result says "go".

---

## 2. Day 0 (tonight, about 90 minutes)

### Step 1: Make the repo
- [x] 1. Create a public GitHub repo named `dbeval`.
- [x] 2. Add the folders from section 1 (empty folders need a `.gitkeep` file).
- [x] 3. Write `README.md` with three things: the one-line pitch, the decision rule (section 10), and a status line.

One-line pitch to paste:

> Which data-agent context layer works best on *your* database? A neutral head-to-head, starting with Postgres.

### Step 2: Start Postgres
- [x] Create `docker-compose.yml` and start Postgres (`docker compose up -d` on port 5433).

### Step 3: Create the databases and a read-only user
- [x] Create `db/init.sql`.
- [x] Run `db/init.sql` to create `olist`, `appdb`, and role `reader` with read-only permissions across both databases. Verified connections.

### Step 4: Check what each tool can do
- [x] Check ktx, Datus and Wren docs/README for Postgres, headless/MCP execution, and LLM providers (recorded in `notes/<tool>.md`).
- [ ] Record setup times and first impressions as each tool is installed.

### Step 5: Load the Olist database
- [x] 1. Downloaded the Olist dataset from Kaggle via `kagglehub` directly into `data/`.
- [x] 2. Wrote `db/load_olist.py` to loop over CSV files and load them into `olist` database tables without foreign keys.
- [x] 3. Ran `db/load_olist.py` and verified row counts (`orders`: 99,441 rows; `geolocation`: 1,000,163 rows; etc.). Verified `reader` role query access.

### Step 6: Look at ktx once
- [x] Installed `@kaelio/ktx@0.16.0` globally and verified managed Python runtime.
- [x] Initialized ktx project (`ktx_olist`), connected to `olist` Postgres database, tested connection and verified read-only SQL queries (`SELECT count(*) FROM orders` -> `99441`).
- [x] Recorded setup log, caveats, and first impressions in `notes/ktx.md`.

**Day 0 is DONE!** The repo is public, Postgres is running, both databases exist, Olist is loaded with 9 verified tables, each tool has a notes file, and initial ktx setup was run and documented.

---

## 3. Day 1: the second database and the baseline

### Step 1: Build `appdb`
- [x] Wrote `db/seed_appdb.py` incorporating SaaS schema traps (soft deletes, test accounts, currency cents, cancellations vs churn, upgrade chains, unkeyed refunds and events).
- [x] Ran `db/seed_appdb.py` to seed 2,000 accounts, 6,976 users, 2,084 subscriptions, 28,914 invoices, 1,112 refunds, and 86,261 events. Verified `reader` role access.

### Step 2: Write the baseline runner
- [x] Wrote `runners/baseline.py`: reads schema + keys + 3 distinct samples per column, builds prompt, enforces read-only SQL, runs with statement timeout and row limit.
- [x] Created `questions/smoke.yaml` with 10 questions (5 Olist, 5 appdb).
- [x] Verified schema inspection on both `olist` and `appdb` (`--show-schema`).

### Step 3: Try it on 5 hand-written questions per database
- [x] Configured LLM provider (Groq `openai/gpt-oss-120b`) in `.env`.
- [x] Ran `python runners/baseline.py --smoke questions/smoke.yaml` across all 10 smoke questions (5 Olist, 5 appdb).
- [x] Inspected generated SQL and results saved to `results/raw/smoke_baseline.json`. Discovered critical baseline traps on SaaS metrics (test accounts included, soft deletes counted, unnetted refunds in revenue, and subscription upgrades counted as churn).

**Day 1 is DONE!** The second database (`appdb`) is built and seeded with traps, the baseline runner works end-to-end against both databases, and the smoke tests revealed clear baseline failure modes to evaluate on Day 2.

---

## 4. Day 2: the question suite

Aim for about 40 validated questions per database.

### Step 1: Write the questions
Mix for each database:

| Type | Count | Example |
|---|---|---|
| Simple lookups | 10 | How many orders were delivered in 2018? |
| Metric questions | 15 | What was net revenue last quarter? |
| Multi-join questions | 10 | Which sellers had the most late deliveries per category? |
| Ambiguous questions | 5 | Who are our best customers? |

Write 15 yourself, thinking like a business person. Have an LLM draft the rest, and read every one.

### Step 1: Write the questions
- [x] Created `docs/business_rules.md` documenting answer-key rules for both databases.
- [x] Drafted questions in `questions/drafts/appdb.yaml` (22 questions + 2 ambiguous) and `questions/drafts/olist.yaml` (12 questions + 1 ambiguous).
- [x] Verified all hand-written SQL queries execute cleanly against seeded Postgres databases with `python scorer/validate_gold.py --skip-oracle`.

### Step 2: Create gold answers
- [x] Built `scorer/compare.py` (order-agnostic, column-agnostic, allows extra candidate columns, 2-decimal tolerance) and verified with `python scorer/test_compare.py`.
- [x] Built dual-oracle validation harness in `scorer/validate_gold.py` using `oracle_a` (`openai/gpt-oss-120b`) and `oracle_b` (`qwen/qwen3.8-27b`).
- [x] Ran validation against `olist`: 10 validated, 3 disputed (`olist-002`, `olist-007`, `olist-012` over status filtering on non-sales/order actions).
- [x] Ran validation against `appdb`: 22 validated, 2 disputed (`appdb-017` over grouping vs scalar count wording, and `appdb-020` over tie-breaking order among equal net-paying accounts).

**Day 2 is done:** Question drafts, business rules, comparison scorer, and dual-oracle validation are complete and documented. Disputed questions isolated in `questions/disputed/`.

---

## 5. Day 3: build each tool's layer (out of the box)

For ktx, Datus and Wren, on both databases:

1. Start a timer.
2. Follow the docs and accept the defaults. **Make no manual edits.**
3. Write down every manual step and every problem in `notes/<tool>.md`.
4. Stop the timer when the tool can answer a first question. Record the time.

If a tool fails on a database, record why. A tool that is hard to set up is a result too.

**Day 3 is done when:** each tool has a layer on each database, or a written failure reason.

---

## 6. Day 4: runners, scorer, first full run

### Step 1: Write one runner per tool
Each runner has one function: `answer(question) -> rows`. How it works inside depends on the tool (a command, an API call, or MCP). Add the files `runners/ktx_run.py`, `runners/datus_run.py` and `runners/wren_run.py`.

### Step 2: Write the scorer
`scorer/compare.py` decides whether two answers match:

```python
def normalize(rows):
    out = []
    for row in rows:
        out.append(tuple(
            round(v, 2) if isinstance(v, float) else str(v)
            for v in row
        ))
    return sorted(out)

def same(a, b):
    return normalize(a) == normalize(b)
```

This ignores row order and tiny rounding differences. It does not forgive different column order, which is fine for now.

### Step 3: Write the suite runner
`scorer/run_suite.py` does this for every system, database and question:

1. Run the question through the runner.
2. Compare to the gold result with `same()`.
3. Record: system, database, question id, pass or fail, the SQL, error text, seconds, and token cost.
4. Write one CSV to `results/raw/`.

### Step 4: Run everything 3 times
LLMs are not perfectly steady, even at temperature 0. Three runs per question show how steady each tool is.

**Day 4 is done when:** `results/raw/` has CSVs for every system on both databases.

---

## 7. Day 5: the 30-minute human review

Now give each tool a fair chance to improve.

1. Set a 30-minute timer **per tool, per database**.
2. Open the tool's generated layer (descriptions, joins, metrics).
3. Fix what is obviously wrong: wrong join, missing metric definition, bad description.
4. Log every change in `notes/<tool>.md`.
5. Re-run the whole suite and save to `results/raw/` with `reviewed` in the file name.

The same time budget for every tool is what keeps this fair.

**Day 5 is done when:** you have before and after numbers for each tool.

---

## 8. Day 6: understand why things failed

Go through every failed question and give it one label:

- wrong join
- wrong metric definition
- wrong filter (for example, forgot to exclude test accounts)
- wrong grain (counted rows instead of customers)
- other

Add a `failure_type` column to your results. Then look at:

- Questions every system failed (probably a bad gold answer or a hard question)
- Questions only one system failed
- The disputed questions
- Any failure caused by a setup problem rather than quality. Mark these separately so you do not blame the tool unfairly.

**Day 6 is done when:** every failure has a label and you have a count per tool.

---

## 9. Day 7: the write-up

Write `results/REPORT.md` with:

1. What you tested (databases, question counts, model, tool versions)
2. The main table: accuracy per tool per database, before and after review, with counts (for example 31/40, not only 77%)
3. Failure categories per tool
4. Setup time and manual steps per tool
5. Variance between the three runs
6. Caveats: small question set, you know these tools less well than their authors, no foreign keys in Olist
7. The decision (section 10)

Keep the raw CSVs in the repo so others can check your work. Post the report once you are happy with it.

---

## 10. The decision rule

- **Go:** accuracy differs by more than about 10 points between tools on at least one database, or the ranking changes between databases.
- **Pivot:** one tool wins on everything. Then the idea shrinks to regression testing for a single layer, which is weaker.
- **Stop:** no tool beats the plain baseline by much. Then the idea that a layer helps is in doubt on your data. You still keep a solid portfolio project.

Write which one you chose, and why, at the bottom of `results/REPORT.md`.

---

## 11. Rules to keep it honest

- Same model, temperature 0, same read-only user, same timeout and row limit for every tool.
- Write down the exact version of every tool.
- Do not tune one tool more than another.
- Report counts, not just percentages. 40 questions is small.
- Run first by hand, automate second. Do not spend the week polishing the harness.
