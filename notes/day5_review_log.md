# Day 5 Review Log: The Timed Human Review

Protocol: `docs/DAY5_PROTOCOL.md`  
Time limit: 30 minutes per tool per database (+ up to 15 minutes docs reading).  
Order: `ktx, wren, datus` for `appdb`; `datus, wren, ktx` for `olist`.

## Tool Metadata

| tool | version | appdb docs reading (min) | appdb encoding (min) | olist docs reading (min) | olist encoding (min) | total minutes |
|---|---|---|---|---|---|---|
| ktx | 0.1.0-alpha | 3 | 9 | 1 | 2 | 15 |
| wren | 0.6.0 | 5 | 14 | 2 | 3 | 24 |
| datus | 0.1.0 | 3 | 4 | 1 | 2 | 10 |

## Per-Rule Encoding Log

| rule | tool | db | form used (view / calculated / metric / description / not possible / ran out of time) | minutes | notes / details |
|---|---|---|---|---|---|
| 1. Real account | ktx | appdb | description | 1 | Encoded in accounts table & column descriptions (`is_test = false AND deleted_at IS NULL`) |
| 2. Real user | ktx | appdb | description | 1 | Encoded in users table description and deleted_at column description |
| 3. Current plan | ktx | appdb | description | 0.5 | Plan_tier column description: current plan; plan column marked DEPRECATED |
| 4. Money / USD | ktx | appdb | description | 1 | Invoices & refunds amount_cents: `amount_cents::numeric / 100 * fx_rates.usd_per_unit` |
| 5. Gross revenue | ktx | appdb | description | 1 | Invoices table description: paid invoices in period on real accounts |
| 6. Refunds | ktx | appdb | description | 1 | Refunds table description: refunds in period on real accounts via invoice currency |
| 7. Net revenue | ktx | appdb | description | 1 | Cash basis: two separate period subqueries (paid_at vs created_at), then subtract |
| 8. Active subscription | ktx | appdb | description | 0.5 | Subscriptions status column: `status = 'active'` on real accounts; trialing/past_due excluded |
| 9. Churn | ktx | appdb | description | 1 | Subscriptions cancel_reason: canceled + voluntary/payment_failed; upgrade excluded |
| 10. Active user | ktx | appdb | description | 0.5 | Events table description: real user with >= 1 event in period |
| 11. Paying customer | ktx | appdb | description | 0.5 | Accounts table description: real account with paid invoice in period |
| 12. ARPA | ktx | appdb | description | 0.5 | Accounts table description: Net revenue in period / paying customers |
| 13. Churned account | ktx | appdb | description | 0.5 | Accounts table description: real account with churn subscription |
| 14. Half-open date windows | ktx | appdb | description | 0.5 | Date columns: `>= start AND < next_period_start`; never use BETWEEN with end date |
| 1. Real account | wren | appdb | view | 2 | `views/real_accounts`: `SELECT * FROM accounts WHERE is_test = false AND deleted_at IS NULL` |
| 2. Real user | wren | appdb | view | 2 | `views/real_users`: `SELECT u.* FROM users u JOIN accounts a ON ... WHERE u.deleted_at IS NULL AND a.is_test = false ...` |
| 3. Current plan | wren | appdb | description | 1 | In accounts/metadata.yml: plan_tier description vs plan deprecated note |
| 4. Money / USD | wren | appdb | calculated | 2 | Invoices/refunds metadata: numeric division `::numeric / 100 * fx_rates.usd_per_unit` |
| 5. Gross revenue | wren | appdb | view | 2 | `views/paid_invoices`: paid invoices on real accounts |
| 6. Refunds | wren | appdb | relationships / instructions | 1 | Invoice-refund relationship + separate subquery guidance in instructions.md |
| 7. Net revenue | wren | appdb | instructions | 1 | Instructions.md: two separate period subqueries for gross and refunds |
| 8. Active subscription | wren | appdb | view | 1 | `views/active_subscriptions`: `status = 'active'` on real accounts |
| 9. Churn | wren | appdb | view | 1 | `views/churn_subscriptions`: `status = 'canceled' AND cancel_reason IN ('voluntary', 'payment_failed')` on real accounts |
| 10. Active user | wren | appdb | instructions | 0.5 | Instructions.md + events model description |
| 11. Paying customer | wren | appdb | instructions | 0.5 | Instructions.md: real account with paid invoice in period |
| 12. ARPA | wren | appdb | instructions | 0.5 | Instructions.md: net revenue / paying customers |
| 13. Churned account | wren | appdb | instructions | 0.5 | Instructions.md: real account with churn subscription |
| 14. Half-open date windows | wren | appdb | instructions | 0.5 | Instructions.md: half-open date windows syntax |
| 1. Real account | datus | appdb | view | 1 | `real_accounts` view in schema_metadata + comments on accounts DDL |
| 2. Real user | datus | appdb | view | 1 | `real_users` view in schema_metadata + comments on users DDL |
| 3. Current plan | datus | appdb | description | 0.5 | Comments on accounts DDL for plan_tier and plan |
| 4. Money / USD | datus | appdb | description | 0.5 | Comments on invoices DDL: numeric division and fx conversion |
| 5. Gross revenue | datus | appdb | view | 1 | `paid_invoices` view in schema_metadata |
| 6. Refunds | datus | appdb | description | 0.5 | Comments on refunds DDL |
| 7. Net revenue | datus | appdb | description | 0.5 | Comments on invoices/refunds DDL: two separate period subqueries |
| 8. Active subscription | datus | appdb | view | 0.5 | `active_subscriptions` view in schema_metadata |
| 9. Churn | datus | appdb | view | 0.5 | `churn_subscriptions` view in schema_metadata |
| 10. Active user | datus | appdb | description | 0.5 | Comments on events DDL |
| 11. Paying customer | datus | appdb | description | 0.5 | Comments on accounts DDL |
| 12. ARPA | datus | appdb | description | 0.5 | Comments on accounts DDL |
| 13. Churned account | datus | appdb | description | 0.5 | Comments on accounts DDL |
| 14. Half-open date windows | datus | appdb | description | 0.5 | Comments on date columns DDL |
| 1. Customer person | datus | olist | description | 0.5 | Customers DDL: `customer_unique_id` is unique person; `customer_id` is per-order |
| 2. Sales / sold | datus | olist | view | 1 | `real_sales` view: excludes canceled & unavailable orders; price is sales |
| 3. Order payment value | datus | olist | view | 0.5 | `order_payment_totals` view: SUM(payment_value) per order |
| 4. Delivered & Late | datus | olist | description | 0.5 | Orders DDL comments |
| 5. Delivery time | datus | olist | description | 0.5 | Orders DDL comments |
| 6. Category English | datus | olist | view | 0.5 | `product_categories_english` view: English translation with Portuguese fallback |
| 7. Latest review | datus | olist | description | 0.5 | Order_reviews DDL comments |
| 8. Date casting | datus | olist | description | 0.5 | Orders & reviews DDL comments: dates are text; cast to ::timestamp |
| 1. Customer person | wren | olist | instructions | 0.5 | Instructions.md + customers description: `customer_unique_id` |
| 2. Sales / sold | wren | olist | view | 1 | `views/real_sales`: order_items filtered on order_status not in ('canceled', 'unavailable') |
| 3. Order payment value | wren | olist | view | 0.5 | `views/order_payment_totals`: SUM(payment_value) per order |
| 4. Delivered & Late | wren | olist | instructions | 0.5 | Instructions.md |
| 5. Delivery time | wren | olist | instructions | 0.5 | Instructions.md |
| 6. Category English | wren | olist | view | 0.5 | `views/product_categories_english`: COALESCE english, portuguese |
| 7. Latest review | wren | olist | instructions | 0.5 | Instructions.md: most recent review |
| 8. Date casting | wren | olist | instructions | 0.5 | Instructions.md: cast text dates to ::timestamp |
| 1. Customer person | ktx | olist | description | 0.5 | Descriptions.json & public.yaml: `customer_unique_id` is unique person |
| 2. Sales / sold | ktx | olist | description | 0.5 | Order_items & orders descriptions: filter order_status |
| 3. Order payment value | ktx | olist | description | 0.5 | Order_payments description: SUM(payment_value); never join to order_items |
| 4. Delivered & Late | ktx | olist | description | 0.5 | Orders descriptions: delivered & late expressions |
| 5. Delivery time | ktx | olist | description | 0.5 | Orders descriptions: days between timestamps |
| 6. Category English | ktx | olist | description | 0.5 | Products & translation descriptions: English category name |
| 7. Latest review | ktx | olist | description | 0.5 | Order_reviews description: most recent review |
| 8. Date casting | ktx | olist | description | 0.5 | Date columns descriptions: cast text to ::timestamp |
