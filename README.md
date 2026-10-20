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
