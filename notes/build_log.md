# Day 3: Out-of-the-Box Build Log

Track the automated layer generation for each tool and database.
**Rules:**
- Model: `codestral-2508` via Mistral AI
- Database user: `reader` (read-only)
- No manual edits to generated layers
- No business rules consulted (`docs/business_rules.md` strictly withheld)

| Tool | Database | Version | Start Time | End Time | Minutes | Embedding Model | Manual Steps | Tokens Used | Errors / Status |
|---|---|---|---|---|---|---|---|---|---|
| ktx | olist | `@kaelio/ktx@0.16.0` | 19:40 | 19:55 | 15 min | `all-MiniLM-L6-v2` (local) | None (CLI quickstart) | ~18.5k (enrichment) | Success. 9 tables ingested. |
| ktx | appdb | `@kaelio/ktx@0.16.0` | 20:15 | 20:35 | 20 min | `all-MiniLM-L6-v2` (local) | None (CLI quickstart) | ~14.2k (enrichment) | Success. 7 tables ingested. |
| Datus | olist | `datus-agent 0.4.3` | 22:45 | 23:25 | 40 min | `all-MiniLM-L6-v2-onnx` (FastEmbed) | Installed `datus-postgresql`, fixed SQLAlchemy | ~8.0k (schema+smoke) | Success. Schema indexed in LanceDB. |
| Datus | appdb | `datus-agent 0.4.3` | 23:25 | 23:35 | 10 min | `all-MiniLM-L6-v2-onnx` (FastEmbed) | Reused `conf/agent.yml` | ~8.0k (schema+smoke) | Success. Schema indexed in LanceDB. |
| Wren AI | olist | `wren-engine 0.6.0` | 01:25 | 01:53 | 28 min | MDL format | Installed `wren-engine` + `psycopg` | 0 (pure schema compiler) | Success. 9 models compiled to `target/mdl.json`. |
| Wren AI | appdb | `wren-engine 0.6.0` | 01:50 | 01:55 | 5 min | MDL format | Scaffolded and compiled | 0 (pure schema compiler) | Success. 7 models compiled to `target/mdl.json`. |

---

## Detailed Notes & Throwaway Smoke Queries (3 per tool/db)

### 1. ktx
- **Embedding Provider:** Local sentence-transformers `all-MiniLM-L6-v2` via internal daemon.
- **Layers Exported:** `layers/ktx/olist/` and `layers/ktx/appdb/` containing raw source dumps and semantic layer yaml definitions.

#### olist
- **Smoke 1 (Count):** `SELECT count(*) FROM orders;`
  - Result: `99441` (Success)
- **Smoke 2 (Avg):** `SELECT round(avg(payment_value)::numeric, 2) FROM order_payments;`
  - Result: `154.10` (Success)
- **Smoke 3 (Join):** `SELECT s.seller_state, count(*) FROM order_items oi JOIN sellers s ON s.seller_id = oi.seller_id GROUP BY s.seller_state ORDER BY count(*) DESC LIMIT 3;`
  - Result: `[('SP', 80342), ('MG', 8827), ('PR', 8671)]` (Success)

#### appdb
- **Smoke 1 (Count):** `SELECT count(*) FROM accounts;`
  - Result: `2000` (Success)
- **Smoke 2 (Avg):** `SELECT round(avg(amount_cents)::numeric / 100, 2) FROM invoices;`
  - Result: `684.81` (Success)
- **Smoke 3 (Join):** `SELECT a.plan_tier, count(*) FROM subscriptions s JOIN accounts a ON a.id = s.account_id GROUP BY a.plan_tier;`
  - Result: `[('scale', 246), ('growth', 627), ('starter', 1211)]` (Success)

---

### 2. Datus
- **Embedding Provider:** FastEmbed ONNX `all-MiniLM-L6-v2-onnx` (free local embedding).
- **Execution Interface:** `PrintModeRunner` headless runner with `codestral-2508`.
- **Layers Exported:** `layers/datus/olist/` and `layers/datus/appdb/` containing `agent.yml` and LanceDB index artifacts.

#### olist
- **Smoke 1 (Count):** `SELECT COUNT(*) AS total_orders FROM orders;`
  - DB Result: `99441` (Success, 2653 tokens in / 13 out)
- **Smoke 2 (Avg):** `SELECT AVG(payment_value) AS average_payment_value FROM order_payments;`
  - DB Result: `154.10` (Success, 2656 tokens in / 18 out)
- **Smoke 3 (Join):** `SELECT seller_state, COUNT(order_items.order_id) AS order_count FROM sellers JOIN order_items ON sellers.seller_id = order_items.seller_id GROUP BY seller_state ORDER BY order_count DESC LIMIT 3;`
  - DB Result: `[('SP', 80342), ('MG', 8827), ('PR', 8671)]` (Success, 2668 tokens in / 62 out)

#### appdb
- **Smoke 1 (Count):** `SELECT COUNT(*) FROM accounts;`
  - DB Result: `2000` (Success, 2653 tokens in / 10 out)
- **Smoke 2 (Avg):** `SELECT AVG(total_amount) AS average_invoice_amount FROM invoices;`
  - DB Result: Error: `column "total_amount" does not exist` (Expected baseline failure without business rules; real column is `amount_cents`)
- **Smoke 3 (Join):** `SELECT account_plan_tier, COUNT(*) AS subscription_count FROM subscriptions GROUP BY account_plan_tier;`
  - DB Result: Error: `column "account_plan_tier" does not exist` (Expected baseline failure; missed explicit join with `accounts`)

---

### 3. Wren AI
- **Embedding / Semantic Format:** Modeling Definition Language (MDL) compiled into `target/mdl.json`.
- **Connector:** Wren native Postgres connector via Ibis (`ibis-framework==10.8.0`, `psycopg==3.3.6`).
- **Layers Exported:** `layers/wren/olist/` and `layers/wren/appdb/` containing `wren_project.yml`, `models/`, `relationships.yml`, and `target/mdl.json`.

#### olist
- **Smoke 1 (Count):** `SELECT count(*) FROM orders;`
  - Result: `99441` (Success, 0.160s)
- **Smoke 2 (Avg):** `SELECT round(avg(payment_value)::numeric, 2) FROM order_payments;`
  - Result: `154.10` (Success, 0.287s)
- **Smoke 3 (Join):** `SELECT s.seller_state, count(*) FROM order_items oi JOIN sellers s ON s.seller_id = oi.seller_id GROUP BY s.seller_state ORDER BY count(*) DESC LIMIT 3;`
  - Result: `[('SP', 80342), ('MG', 8827), ('PR', 8671)]` (Success, 0.987s)

#### appdb
- **Smoke 1 (Count):** `SELECT count(*) FROM accounts;`
  - Result: `2000` (Success, 0.066s)
- **Smoke 2 (Avg):** `SELECT round(avg(amount_cents)::numeric / 100, 2) FROM invoices;`
  - Result: `684.81` (Success, 0.081s)
- **Smoke 3 (Join):** `SELECT a.plan_tier, count(*) FROM subscriptions s JOIN accounts a ON a.id = s.account_id GROUP BY a.plan_tier;`
  - Result: `[('scale', 246), ('growth', 627), ('starter', 1211)]` (Success, 0.058s)
