# dbeval Failure Attribution Report

Source: `results/raw/suite_results_with_controls.csv`

Failures are categorized by automated comparison of candidate SQL against the gold SQL rule requirements and PostgreSQL engine errors.


## Database: appdb

| Failure Label | baseline | baseline_rules | datus | ktx | schema_only | schema_true_joins | wren |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `missing:cancel_reason+soft_delete` | 0 | 0 | 0 | 0 | 1 | 1 | 2 |
| `missing:cancel_reason+soft_delete+test_filter` | 11 | 0 | 12 | 12 | 7 | 5 | 10 |
| `missing:cancel_reason+test_filter` | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `missing:cents_conversion+fx_join+refund_netting+soft_delete+test_filter` | 0 | 0 | 0 | 1 | 2 | 0 | 0 |
| `missing:cents_conversion+paid_invoice_filter+soft_delete+test_filter` | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `missing:cents_conversion+refund_netting+soft_delete+test_filter` | 1 | 0 | 0 | 0 | 0 | 2 | 0 |
| `missing:cents_conversion+soft_delete` | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| `missing:cents_conversion+soft_delete+test_filter` | 3 | 0 | 3 | 8 | 5 | 3 | 5 |
| `missing:fx_join+refund_netting+soft_delete` | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| `missing:fx_join+soft_delete+test_filter` | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| `missing:paid_invoice_filter+soft_delete+test_filter` | 1 | 0 | 6 | 3 | 2 | 2 | 3 |
| `missing:plan_tier+soft_delete` | 0 | 0 | 0 | 0 | 2 | 1 | 0 |
| `missing:plan_tier+soft_delete+test_filter` | 4 | 0 | 3 | 6 | 0 | 2 | 6 |
| `missing:plan_tier+test_filter` | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| `missing:refund_netting+soft_delete` | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `missing:refund_netting+soft_delete+test_filter` | 2 | 0 | 3 | 0 | 0 | 1 | 0 |
| `missing:soft_delete` | 1 | 0 | 0 | 0 | 0 | 1 | 6 |
| `missing:soft_delete+test_filter` | 52 | 4 | 45 | 47 | 29 | 29 | 40 |
| `missing:test_filter` | 3 | 0 | 3 | 2 | 4 | 5 | 5 |
| `other` | 0 | 19 | 0 | 0 | 0 | 0 | 0 |
| `sql_error:grouping_error` | 3 | 2 | 3 | 2 | 4 | 2 | 3 |
| `sql_error:undefined_function` | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| **TOTAL FAILURES** | 82 | 25 | 81 | 84 | 58 | 56 | 84 |


## Database: olist

| Failure Label | baseline | baseline_rules | datus | ktx | schema_only | schema_true_joins | wren |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `missing:customer_unique_id` | 9 | 0 | 3 | 3 | 6 | 6 | 3 |
| `missing:date_cast+sales_status_filter` | 2 | 0 | 3 | 2 | 2 | 1 | 0 |
| `missing:sales_status_filter` | 0 | 0 | 0 | 1 | 0 | 1 | 3 |
| `other` | 4 | 3 | 4 | 3 | 2 | 2 | 3 |
| `sql_error:syntax_error` | 0 | 2 | 3 | 3 | 2 | 2 | 3 |
| `sql_error:undefined_function` | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| **TOTAL FAILURES** | 17 | 5 | 13 | 12 | 12 | 12 | 12 |


## Detailed Inspection: `other` and `baseline_rules` Failures

Below are questions where `failure_label` is `other` or where `baseline_rules` failed:


### [olist] olist-006 (baseline) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(op.payment_value) AS average_payment_value
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(t.v)::numeric, 2) FROM (
  SELECT p.order_id, SUM(p.payment_value) AS v
  FROM order_payments p JOIN orders o ON o.order_id = p.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY p.order_id) t
```


### [olist] olist-006 (ktx) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(op.payment_value) AS average_payment_value
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(t.v)::numeric, 2) FROM (
  SELECT p.order_id, SUM(p.payment_value) AS v
  FROM order_payments p JOIN orders o ON o.order_id = p.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY p.order_id) t
```


### [olist] olist-006 (datus) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(op.payment_value) AS average_payment_value
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(t.v)::numeric, 2) FROM (
  SELECT p.order_id, SUM(p.payment_value) AS v
  FROM order_payments p JOIN orders o ON o.order_id = p.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY p.order_id) t
```


### [olist] olist-006 (wren) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(op.payment_value) AS average_payment_value
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(t.v)::numeric, 2) FROM (
  SELECT p.order_id, SUM(p.payment_value) AS v
  FROM order_payments p JOIN orders o ON o.order_id = p.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY p.order_id) t
```


### [olist] olist-008 (baseline) - Label: `other`

**Question:** Of all delivered orders, what percentage included at least one credit card payment?


```sql
-- Candidate SQL:
SELECT
    ROUND(100.0 * COUNT(DISTINCT o.order_id) / NULLIF(COUNT(DISTINCT CASE WHEN op.payment_type = 'credit_card' THEN o.order_id END), 0), 2) AS percentage_with_credit_card
FROM
    orders o
JOIN
    order_payments op ON o.order_id = op.order_id
WHERE
    o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(100.0 * COUNT(DISTINCT p.order_id) /
       (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'), 2)
FROM order_payments p JOIN orders o ON o.order_id = p.order_id
WHERE o.order_status = 'delivered' AND p.payment_type = 'credit_card'
```


### [olist] olist-008 (datus) - Label: `other`

**Question:** Of all delivered orders, what percentage included at least one credit card payment?


```sql
-- Candidate SQL:
SELECT
    ROUND(
        (COUNT(DISTINCT op.order_id) * 100.0 / NULLIF(COUNT(DISTINCT o.order_id), 0)),
        2
    ) AS percentage_credit_card_orders
FROM
    orders o
JOIN
    order_payments op ON o.order_id = op.order_id
WHERE
    o.order_status = 'delivered'
    AND op.payment_type = 'credit_card'
```

```sql
-- Gold SQL:
SELECT ROUND(100.0 * COUNT(DISTINCT p.order_id) /
       (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'), 2)
FROM order_payments p JOIN orders o ON o.order_id = p.order_id
WHERE o.order_status = 'delivered' AND p.payment_type = 'credit_card'
```


### [olist] olist-006 (schema_only) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(op.payment_value) AS average_payment_value
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(t.v)::numeric, 2) FROM (
  SELECT p.order_id, SUM(p.payment_value) AS v
  FROM order_payments p JOIN orders o ON o.order_id = p.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY p.order_id) t
```


### [olist] olist-006 (schema_true_joins) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(op.payment_value) AS avg_payment_value
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(t.v)::numeric, 2) FROM (
  SELECT p.order_id, SUM(p.payment_value) AS v
  FROM order_payments p JOIN orders o ON o.order_id = p.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY p.order_id) t
```


### [olist] olist-006 (baseline_rules) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(payment_value) AS avg_payment_value
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(t.v)::numeric, 2) FROM (
  SELECT p.order_id, SUM(p.payment_value) AS v
  FROM order_payments p JOIN orders o ON o.order_id = p.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY p.order_id) t
```


### [olist] olist-007 (baseline_rules) - Label: `other`

**Question:** How many customers have ordered more than once?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT customer_unique_id) AS customers_ordered_more_than_once
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    GROUP BY customer_id
    HAVING COUNT(order_id) > 1
)
```

```sql
-- Gold SQL:
SELECT COUNT(*) FROM (
  SELECT c.customer_unique_id
  FROM customers c JOIN orders o ON o.customer_id = c.customer_id
  GROUP BY c.customer_unique_id
  HAVING COUNT(DISTINCT o.order_id) > 1) t
```


### [appdb] appdb-003 (baseline_rules) - Label: `missing:soft_delete+test_filter`

**Question:** How many accounts signed up in 2025?


```sql
-- Candidate SQL:
SELECT COUNT(*) AS account_count
FROM accounts
WHERE EXTRACT(YEAR FROM created_at) = 2025
```

```sql
-- Gold SQL:
SELECT COUNT(*) FROM accounts
WHERE is_test = false AND deleted_at IS NULL
  AND created_at >= '2025-01-01 00:00:00+00' AND created_at < '2026-01-01 00:00:00+00'
```


### [appdb] appdb-008 (baseline_rules) - Label: `other`

**Question:** What was our net revenue in USD in Q3 2026?


```sql
-- Candidate SQL:
SELECT
    SUM(
        CASE
            WHEN invoices.currency = 'USD' THEN invoices.amount_cents / 100.0
            ELSE invoices.amount_cents / 100.0 * fx_rates.usd_per_unit
        END
    ) -
    SUM(
        CASE
            WHEN invoices.currency = 'USD' THEN refunds.amount_cents / 100.0
            ELSE refunds.amount_cents / 100.0 * fx_rates.usd_per_unit
        END
    ) AS net_revenue
FROM
    invoices
JOIN
    accounts ON invoices.account_id = accounts.id
LEFT JOIN
    fx_rates ON invoices.currency = fx_rates.currency
LEFT JOIN
    refunds ON invoices.id = refunds.invoice_id
WHERE
    accounts.is_test = false
    AND accounts.deleted_at IS NULL
    AND invoices.status = 'paid'
    AND invoices.paid_at >= '2026-07-01'
    AND invoices.paid_at < '2026-10-01'
    AND (
        refunds.created_at IS NULL
        OR (
            refunds.created_at >= '2026-07-01'
            AND refunds.created_at < '2026-10-01'
        )
    )
```

```sql
-- Gold SQL:
SELECT ROUND((
  (SELECT COALESCE(SUM(i.amount_cents::numeric / 100 * f.usd_per_unit), 0)
     FROM invoices i JOIN fx_rates f ON f.currency = i.currency
     JOIN accounts a ON a.id = i.account_id
    WHERE i.status = 'paid'
      AND i.paid_at >= '2026-07-01 00:00:00+00' AND i.paid_at < '2026-10-01 00:00:00+00'
      AND a.is_test = false AND a.deleted_at IS NULL)
  -
  (SELECT COALESCE(SUM(r.amount_cents::numeric / 100 * f.usd_per_unit), 0)
     FROM refunds r JOIN invoices i ON i.id = r.invoice_id
     JOIN fx_rates f ON f.currency = i.currency
     JOIN accounts a ON a.id = i.account_id
    WHERE r.created_at >= '2026-07-01 00:00:00+00' AND r.created_at < '2026-10-01 00:00:00+00'
      AND a.is_test = false AND a.deleted_at IS NULL)
), 2)
```


### [appdb] appdb-009 (baseline_rules) - Label: `other`

**Question:** What was our gross revenue in USD in Q3 2026, before refunds?


```sql
-- Candidate SQL:
SELECT
    SUM(i.amount_cents / 100 * fx.usd_per_unit) AS gross_revenue_usd
FROM
    invoices i
JOIN
    accounts a ON i.account_id = a.id
JOIN
    fx_rates fx ON i.currency = fx.currency
WHERE
    i.status = 'paid'
    AND a.is_test = false
    AND a.deleted_at IS NULL
    AND i.paid_at BETWEEN '2026-07-01' AND '2026-09-30'
```

```sql
-- Gold SQL:
SELECT ROUND(SUM(i.amount_cents::numeric / 100 * f.usd_per_unit), 2)
FROM invoices i JOIN fx_rates f ON f.currency = i.currency
JOIN accounts a ON a.id = i.account_id
WHERE i.status = 'paid'
  AND i.paid_at >= '2026-07-01 00:00:00+00' AND i.paid_at < '2026-10-01 00:00:00+00'
  AND a.is_test = false AND a.deleted_at IS NULL
```


### [appdb] appdb-010 (baseline_rules) - Label: `other`

**Question:** How much did we refund in USD in Q3 2026?


```sql
-- Candidate SQL:
SELECT
    SUM(r.amount_cents / 100 * fx.usd_per_unit) AS total_refunded_usd
FROM
    refunds r
JOIN
    invoices i ON r.invoice_id = i.id
JOIN
    accounts a ON i.account_id = a.id
JOIN
    fx_rates fx ON i.currency = fx.currency
WHERE
    a.is_test = false
    AND a.deleted_at IS NULL
    AND r.created_at BETWEEN '2026-07-01' AND '2026-09-30'
```

```sql
-- Gold SQL:
SELECT ROUND(SUM(r.amount_cents::numeric / 100 * f.usd_per_unit), 2)
FROM refunds r JOIN invoices i ON i.id = r.invoice_id
JOIN fx_rates f ON f.currency = i.currency
JOIN accounts a ON a.id = i.account_id
WHERE r.created_at >= '2026-07-01 00:00:00+00' AND r.created_at < '2026-10-01 00:00:00+00'
  AND a.is_test = false AND a.deleted_at IS NULL
```


### [appdb] appdb-012 (baseline_rules) - Label: `other`

**Question:** How many subscriptions churned in the second quarter of 2026?


```sql
-- Candidate SQL:
SELECT COUNT(*) AS churned_subscriptions
FROM subscriptions
JOIN accounts ON subscriptions.account_id = accounts.id
WHERE accounts.is_test = false
  AND accounts.deleted_at IS NULL
  AND subscriptions.status = 'canceled'
  AND subscriptions.cancel_reason IN ('voluntary', 'payment_failed')
  AND subscriptions.canceled_at BETWEEN '2026-04-01' AND '2026-06-30'
```

```sql
-- Gold SQL:
SELECT COUNT(*) FROM subscriptions s JOIN accounts a ON a.id = s.account_id
WHERE s.status = 'canceled' AND s.cancel_reason IN ('voluntary', 'payment_failed')
  AND s.canceled_at >= '2026-04-01 00:00:00+00' AND s.canceled_at < '2026-07-01 00:00:00+00'
  AND a.is_test = false AND a.deleted_at IS NULL
```


### [appdb] appdb-014 (baseline_rules) - Label: `other`

**Question:** How many monthly active users did we have in September 2026?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT u.id) AS monthly_active_users
FROM users u
JOIN accounts a ON u.account_id = a.id
JOIN events e ON u.id = e.user_id
WHERE a.is_test = false
  AND a.deleted_at IS NULL
  AND u.deleted_at IS NULL
  AND e.occurred_at BETWEEN '2026-09-01' AND '2026-09-30'
```

```sql
-- Gold SQL:
SELECT COUNT(DISTINCT e.user_id) FROM events e
JOIN users u ON u.id = e.user_id JOIN accounts a ON a.id = u.account_id
WHERE e.occurred_at >= '2026-09-01 00:00:00+00' AND e.occurred_at < '2026-10-01 00:00:00+00'
  AND u.deleted_at IS NULL AND a.is_test = false AND a.deleted_at IS NULL
```


### [appdb] appdb-015 (baseline_rules) - Label: `other`

**Question:** What was the average paid invoice amount in USD in 2026?


```sql
-- Candidate SQL:
SELECT AVG(i.amount_cents / 100 * fx.usd_per_unit) AS average_paid_invoice_amount_usd
FROM invoices i
JOIN accounts a ON i.account_id = a.id
JOIN fx_rates fx ON i.currency = fx.currency
WHERE i.status = 'paid'
  AND a.is_test = false
  AND a.deleted_at IS NULL
  AND EXTRACT(YEAR FROM i.paid_at) = 2026
```

```sql
-- Gold SQL:
SELECT ROUND(AVG(i.amount_cents::numeric / 100 * f.usd_per_unit), 2)
FROM invoices i JOIN fx_rates f ON f.currency = i.currency
JOIN accounts a ON a.id = i.account_id
WHERE i.status = 'paid'
  AND i.paid_at >= '2026-01-01 00:00:00+00' AND i.paid_at < '2027-01-01 00:00:00+00'
  AND a.is_test = false AND a.deleted_at IS NULL
```


### [appdb] appdb-020 (baseline_rules) - Label: `sql_error:grouping_error`

**Question:** How many accounts paid us more than 2000 USD in 2026 after refunds?


**Error:** `ProgrammingError: (psycopg2.errors.GroupingError) aggregate function calls cannot be nested
LINE 11: HAVING SUM((i.amount_cents - COALESCE(SUM(r.amount_cents), 0...
                                   `


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT a.id) AS accounts_paid_more_than_2000_usd
FROM accounts a
JOIN invoices i ON a.id = i.account_id
JOIN fx_rates f ON i.currency = f.currency
LEFT JOIN refunds r ON i.id = r.invoice_id
WHERE a.is_test = false
  AND a.deleted_at IS NULL
  AND i.status = 'paid'
  AND i.paid_at BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY a.id
HAVING SUM((i.amount_cents - COALESCE(SUM(r.amount_cents), 0)) * f.usd_per_unit / 100) > 2000
```

```sql
-- Gold SQL:
WITH paid AS (
  SELECT i.account_id, SUM(i.amount_cents::numeric / 100 * f.usd_per_unit) AS v
  FROM invoices i JOIN fx_rates f ON f.currency = i.currency
  WHERE i.status = 'paid'
    AND i.paid_at >= '2026-01-01 00:00:00+00' AND i.paid_at < '2027-01-01 00:00:00+00'
  GROUP BY i.account_id),
ref AS (
  SELECT i.account_id, SUM(r.amount_cents::numeric / 100 * f.usd_per_unit) AS v
  FROM refunds r JOIN invoices i ON i.id = r.invoice_id
  JOIN fx_rates f ON f.currency = i.currency
  WHERE r.created_at >= '2026-01-01 00:00:00+00' AND r.created_at < '2027-01-01 00:00:00+00'
  GROUP BY i.account_id)
SELECT COUNT(*) FROM paid p
JOIN accounts a ON a.id = p.account_id AND a.is_test = false AND a.deleted_at IS NULL
LEFT JOIN ref r ON r.account_id = p.account_id
WHERE p.v - COALESCE(r.v, 0) > 2000
```


### [appdb] appdb-026 (baseline_rules) - Label: `other`

**Question:** What was our average revenue per paying customer in Q3 2026, rounded to 2 decimals?


```sql
-- Candidate SQL:
SELECT ROUND(SUM(i.amount_cents / 100 * fx.usd_per_unit) - SUM(COALESCE(r.amount_cents, 0) / 100 * fx.usd_per_unit) / COUNT(DISTINCT i.account_id), 2) AS arpa
FROM invoices i
JOIN fx_rates fx ON i.currency = fx.currency
LEFT JOIN refunds r ON i.id = r.invoice_id
JOIN accounts a ON i.account_id = a.id
WHERE i.status = 'paid'
AND a.is_test = false
AND a.deleted_at IS NULL
AND i.paid_at BETWEEN '2026-07-01' AND '2026-09-30'
AND i.paid_at >= '2026-07-01'
AND i.paid_at <= '2026-09-30'
```

```sql
-- Gold SQL:
SELECT ROUND((
  (SELECT COALESCE(SUM(i.amount_cents::numeric / 100 * f.usd_per_unit), 0)
     FROM invoices i JOIN fx_rates f ON f.currency = i.currency JOIN accounts a ON a.id = i.account_id
    WHERE i.status = 'paid'
      AND i.paid_at >= '2026-07-01 00:00:00+00' AND i.paid_at < '2026-10-01 00:00:00+00'
      AND a.is_test = false AND a.deleted_at IS NULL)
  -
  (SELECT COALESCE(SUM(r.amount_cents::numeric / 100 * f.usd_per_unit), 0)
     FROM refunds r JOIN invoices i ON i.id = r.invoice_id JOIN fx_rates f ON f.currency = i.currency
     JOIN accounts a ON a.id = i.account_id
    WHERE r.created_at >= '2026-07-01 00:00:00+00' AND r.created_at < '2026-10-01 00:00:00+00'
      AND a.is_test = false AND a.deleted_at IS NULL)
) / (
  SELECT COUNT(DISTINCT i.account_id) FROM invoices i JOIN accounts a ON a.id = i.account_id
   WHERE i.status = 'paid'
     AND i.paid_at >= '2026-07-01 00:00:00+00' AND i.paid_at < '2026-10-01 00:00:00+00'
     AND a.is_test = false AND a.deleted_at IS NULL
), 2)
```


### [appdb] appdb-027 (baseline_rules) - Label: `missing:soft_delete+test_filter`

**Question:** How many accounts have had more than one subscription?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT account_id) AS accounts_with_multiple_subscriptions
FROM subscriptions
WHERE account_id IN (
    SELECT account_id
    FROM subscriptions
    GROUP BY account_id
    HAVING COUNT(id) > 1
)
```

```sql
-- Gold SQL:
SELECT COUNT(*) FROM (
  SELECT s.account_id FROM subscriptions s JOIN accounts a ON a.id = s.account_id
  WHERE a.is_test = false AND a.deleted_at IS NULL
  GROUP BY s.account_id HAVING COUNT(*) > 1) t
```


### [appdb] appdb-031 (baseline_rules) - Label: `other`

**Question:** How many distinct users logged in at least once in Q3 2026?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT e.user_id)
FROM events e
JOIN users u ON e.user_id = u.id
JOIN accounts a ON u.account_id = a.id
WHERE e.event_type = 'login'
  AND e.occurred_at BETWEEN '2026-07-01' AND '2026-09-30'
  AND a.is_test = false
  AND a.deleted_at IS NULL
  AND u.deleted_at IS NULL
```

```sql
-- Gold SQL:
SELECT COUNT(DISTINCT e.user_id) FROM events e
JOIN users u ON u.id = e.user_id JOIN accounts a ON a.id = u.account_id
WHERE e.event_type = 'login'
  AND e.occurred_at >= '2026-07-01 00:00:00+00' AND e.occurred_at < '2026-10-01 00:00:00+00'
  AND u.deleted_at IS NULL AND a.is_test = false AND a.deleted_at IS NULL
```


### [appdb] appdb-033 (baseline_rules) - Label: `other`

**Question:** How much was refunded in USD on invoices issued in Q2 2026, whenever the refund happened?


```sql
-- Candidate SQL:
SELECT
    SUM(r.amount_cents / 100 * fx.usd_per_unit) AS total_refunded_usd
FROM
    refunds r
JOIN
    invoices i ON r.invoice_id = i.id
JOIN
    fx_rates fx ON i.currency = fx.currency
JOIN
    accounts a ON i.account_id = a.id
WHERE
    i.issued_at BETWEEN '2026-04-01' AND '2026-06-30'
    AND a.is_test = false
    AND a.deleted_at IS NULL
```

```sql
-- Gold SQL:
SELECT ROUND(SUM(r.amount_cents::numeric / 100 * f.usd_per_unit), 2)
FROM refunds r JOIN invoices i ON i.id = r.invoice_id
JOIN fx_rates f ON f.currency = i.currency JOIN accounts a ON a.id = i.account_id
WHERE i.issued_at >= '2026-04-01 00:00:00+00' AND i.issued_at < '2026-07-01 00:00:00+00'
  AND a.is_test = false AND a.deleted_at IS NULL
```


### [appdb] appdb-021 (baseline_rules) - Label: `other`

**Question:** How many accounts with an active subscription had no events at all between 2 July and 30 September 2026?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT a.id) AS accounts_with_active_subscription_no_events
FROM accounts a
JOIN subscriptions s ON a.id = s.account_id
LEFT JOIN events e ON a.id = e.account_id
WHERE a.is_test = false
  AND a.deleted_at IS NULL
  AND s.status = 'active'
  AND (e.occurred_at < '2026-07-02' OR e.occurred_at > '2026-09-30' OR e.occurred_at IS NULL)
```

```sql
-- Gold SQL:
SELECT COUNT(DISTINCT s.account_id) FROM subscriptions s JOIN accounts a ON a.id = s.account_id
WHERE s.status = 'active' AND a.is_test = false AND a.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM events e WHERE e.account_id = s.account_id
      AND e.occurred_at >= '2026-07-02 00:00:00+00' AND e.occurred_at < '2026-10-01 00:00:00+00')
```

