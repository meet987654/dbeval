# Datus in dbeval: per-question breakdown

**From:** Meet Prajapati (github.com/meet987654) · **For:** the Datus team · **Date:** 20 Nov 2026
**Source:** [github.com/meet987654/dbeval](https://github.com/meet987654/dbeval), commit `5abd697` (16 Nov 2026). Every number below comes from `results/per_question.csv` and `results/raw/suite_results_all.csv` in that repo.

## How Datus was run (read this first)

- **Not the Datus agent.** The runner (`runners/datus_run.py`) reads Datus's stored files (`schema_metadata.json`, `schema_value.json`, `agent.yml`, and `rules.md` when present), renders them as text, and makes **one** call to `codestral-2508` for the SQL. Datus's own retrieval, tools and execute-and-retry loop were not used.
- **Versions:** `datus-agent 0.4.3`, `datus-postgresql 0.1.9`. That is before the foreign-key fix in `datus-db-adapters#177`, so every Datus layer's DDL has `PRIMARY KEY` but no `FOREIGN KEY` clauses.
- **Three Datus configurations:**
  - `datus`: the layer as Datus generated it.
  - `datus_reviewed`: the layer after a timed review, plus a `rules.md` drop-in. The reviewer copied all 14 appdb rules and all 8 olist rules into it verbatim, so this is close to "prompt rules + Datus DDL and sample values".
  - `datus_reviewed_defonly`: the same review, with the rules written only as comments in the table definitions (no `rules.md`).
- **The reviews were written by an AI agent in timed sessions**, not by someone who knows Datus well. A layer your team writes would probably do better.
- **Sample size:** 32 questions on `appdb` (a synthetic SaaS database with soft deletes, test accounts, cents, FX and refunds) and 18 on `olist` (public e-commerce data). Out-of-box systems ran 2 times, reviewed systems 3 times. One appdb question is worth 3.1 points.

## Scores

| System | appdb (32) | olist (18) |
|---|---|---|
| baseline (raw schema + samples) | 4.00 (12.5%) | 13.00 (72.2%) |
| baseline_rules (rules pasted in prompt) | 28.00 (87.5%) | 15.00 (83.3%) |
| datus (out of box) | 5.00 (15.6%) | 13.00 (72.2%) |
| **datus_reviewed** (with `rules.md`) | **26.33 (82.3%)** | **16.33 (90.7%)** |
| datus_reviewed_defonly (definition comments only) | 25.33 (79.2%) | 14.67 (81.5%) |

Scores are questions answered correctly, averaged over runs. On olist, `datus_reviewed` was the best system in the study. On appdb it was 1.67 questions below prompt rules; the paired 95% CI is [-15.1, +3.6] points (p = 0.688), so that gap is not significant.

## Where datus_reviewed lost points on appdb

It lost 5.67 questions in total. Three of them were missed by every system, prompt rules included.

| Question | datus_reviewed | baseline_rules | What went wrong |
|------------|-----|-----|---------------------|
| appdb-005 Which plan tier has the most active subscriptions? | 0/3 | 2/2 | **SQL error every run:** `column reference "plan_tier" is ambiguous`. Both `subscriptions` and `accounts` have `plan_tier`, and the query used it unqualified. Same in defonly (0/3). |
| appdb-003 How many accounts signed up in 2025? | 1/3 | 2/2 | 2 runs left out the test-account and soft-delete filters. Defonly got 3/3. |
| appdb-017 How many failed invoices were issued in Q3 2026? | 1/3 | 2/2 | 2 runs queried `invoices` alone and never joined `accounts`, so test and deleted accounts were counted. Defonly also 1/3. |
| appdb-013 How many customers upgraded their plan in 2026? | 2/3 | 2/2 | 1 run queried `subscriptions` alone, without the account filters. |
| appdb-020 Accounts that paid > 2,000 USD in 2026 after refunds | 0/3 | 0/2 | Hard for everyone. Nested-aggregate SQL error, dropped refunds, or excluded every account that had a refund. |
| appdb-026 Average revenue per paying customer, Q3 2026 | 0/3 | 0/2 | Hard for everyone. Used gross revenue; refunds were never subtracted. |
| appdb-027 Accounts with more than one subscription | 0/3 | 0/2 | Hard for everyone. Counted test and deleted accounts. |

It gained back 1.0 question on appdb-021 and appdb-030 (3/3 each, where prompt rules got 1/2).

## Where datus_reviewed lost points on olist

| Question | datus_reviewed | baseline_rules | What went wrong |
|------------|-----|-----|---------------------|
| olist-018 Average review score of delivered orders | 0/3 | 0/2 | **SQL error every run:** the model used `or` as a table alias, which is a reserved word. Every system failed this one. |
| olist-014 How many products are in the catalog? | 1/3 | 2/2 | 2 runs added `WHERE product_category_name IS NOT NULL`. A rule was applied where it doesn't belong. |

It beat prompt rules on olist-006 (average payment per delivered order) and olist-007 (customers who ordered more than once), 3/3 versus 0/2. Without `rules.md` both dropped to 0/3.

## Patterns that may be useful to you

1. **Two of the misses are SQL errors that an agent loop would probably catch.** appdb-005 (ambiguous column) and olist-018 (reserved-word alias) failed every run with a Postgres error. An agent that runs the SQL and retries on errors would likely recover both; this one-shot runner never retried. I haven't tested Datus's own agent on them.
2. **Account filters get dropped on child tables.** On appdb-017, 013 and 027 the model queried `invoices` or `subscriptions` without joining `accounts`, so the is-test and soft-delete rules never applied. The layer DDL had no foreign keys (the bug fixed in #177), so the link from `invoices.account_id` to `accounts.id` was not stated anywhere. This is only a hypothesis; a rerun with the fixed adapter would test it.
3. **Rules in `rules.md` helped more than rules in definition comments.** Without `rules.md`, Datus lost 1.0 question on appdb and 1.67 on olist. The clearest case is appdb-008 (net revenue, Q3 2026): with `rules.md` 3/3, definitions only 0/3, where the model fell back to a single `LEFT JOIN refunds` (and once hard-coded FX rates).
4. **Out of box, Datus scored like the raw schema** (5/32 versus 4/32 on appdb). The misses were the business rules (test accounts, soft deletes, cents, refunds), which no tool can infer without being told.

## What I can rerun for you

1. The same 50 questions through the **actual Datus agent**, with whatever config you recommend.
2. The layers rebuilt with the **fixed `datus-postgresql`** (foreign keys included), to test pattern 2.
3. A **layer your team writes**, scored on the same questions and gold SQL.

Every question, gold query and generated SQL is in the repo if you want to check anything yourselves.
