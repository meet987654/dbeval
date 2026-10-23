# dbeval Failure Attribution Report

Source: `results/raw/suite_results_20261023_115601.csv`

Failures are categorized by automated comparison of candidate SQL against the gold SQL rule requirements and PostgreSQL engine errors.


## Database: appdb

| Failure Label | baseline | baseline_rules | datus | ktx | schema_only | schema_true_joins | wren |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `missing:cancel_reason+soft_delete` | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| `missing:cancel_reason+soft_delete+test_filter` | 4 | 0 | 4 | 4 | 3 | 3 | 3 |
| `missing:cents_conversion+paid_invoice_filter+soft_delete+test_filter` | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| `missing:cents_conversion+refund_netting+soft_delete+test_filter` | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `missing:cents_conversion+soft_delete+test_filter` | 1 | 0 | 2 | 2 | 1 | 2 | 1 |
| `missing:fx_join+soft_delete+test_filter` | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| `missing:paid_invoice_filter+soft_delete+test_filter` | 0 | 0 | 2 | 1 | 0 | 0 | 1 |
| `missing:plan_tier+soft_delete` | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `missing:plan_tier+soft_delete+test_filter` | 2 | 0 | 1 | 1 | 2 | 0 | 2 |
| `missing:plan_tier+test_filter` | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `missing:refund_netting+soft_delete` | 0 | 0 | 0 | 1 | 1 | 0 | 1 |
| `missing:refund_netting+soft_delete+test_filter` | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| `missing:soft_delete` | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| `missing:soft_delete+test_filter` | 17 | 1 | 14 | 16 | 17 | 16 | 14 |
| `missing:test_filter` | 1 | 0 | 2 | 1 | 2 | 3 | 1 |
| `other` | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| `sql_error:grouping_error` | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| `sql_error:undefined_function` | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| **TOTAL FAILURES** | 28 | 5 | 27 | 28 | 29 | 28 | 28 |


## Database: olist

| Failure Label | baseline | baseline_rules | datus | ktx | schema_only | schema_true_joins | wren |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `missing:customer_unique_id` | 3 | 0 | 1 | 1 | 3 | 3 | 1 |
| `missing:date_cast+sales_status_filter` | 1 | 0 | 1 | 1 | 1 | 0 | 0 |
| `missing:sales_status_filter` | 0 | 0 | 1 | 0 | 1 | 1 | 1 |
| `other` | 1 | 2 | 2 | 1 | 1 | 1 | 1 |
| `sql_error:runtime_error` | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| `sql_error:syntax_error` | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| **TOTAL FAILURES** | 5 | 3 | 6 | 4 | 7 | 6 | 5 |


## Detailed Inspection: `other` and `baseline_rules` Failures

Below are questions where `failure_label` is `other` or where `baseline_rules` failed:


### [appdb] appdb-020 (baseline_rules) - Label: `sql_error:grouping_error`

**Question:** How many accounts paid us more than 2000 USD in 2026 after refunds?


**Error:** `ProgrammingError: (psycopg2.errors.GroupingError) aggregate function calls cannot be nested
LINE 12: ...cents::numeric / 100 * f.usd_per_unit) - COALESCE(SUM(r.amou...
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
  AND i.paid_at >= '2026-01-01 00:00:00+00'
  AND i.paid_at < '2027-01-01 00:00:00+00'
GROUP BY a.id
HAVING SUM((i.amount_cents::numeric / 100 * f.usd_per_unit) - COALESCE(SUM(r.amount_cents::numeric / 100 * f.usd_per_unit), 0)) > 2000
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
  AND e.id IS NULL
  AND e.occurred_at >= '2026-07-01 00:00:00+00'
  AND e.occurred_at < '2026-10-01 00:00:00+00'
```

```sql
-- Gold SQL:
SELECT COUNT(DISTINCT s.account_id) FROM subscriptions s JOIN accounts a ON a.id = s.account_id
WHERE s.status = 'active' AND a.is_test = false AND a.deleted_at IS NULL
  AND NOT EXISTS (
    SELECT 1 FROM events e WHERE e.account_id = s.account_id
      AND e.occurred_at >= '2026-07-02 00:00:00+00' AND e.occurred_at < '2026-10-01 00:00:00+00')
```


### [appdb] appdb-026 (baseline_rules) - Label: `other`

**Question:** What was our average revenue per paying customer in Q3 2026, rounded to 2 decimals?


```sql
-- Candidate SQL:
SELECT ROUND(SUM(
    CASE
        WHEN invoices.status = 'paid' THEN invoices.amount_cents::numeric / 100 * fx_rates.usd_per_unit
        ELSE 0
    END
) - SUM(
    CASE
        WHEN refunds.id IS NOT NULL THEN refunds.amount_cents::numeric / 100 * fx_rates.usd_per_unit
        ELSE 0
    END
) / COUNT(DISTINCT invoices.account_id), 2) AS arpa
FROM invoices
LEFT JOIN fx_rates ON invoices.currency = fx_rates.currency
LEFT JOIN refunds ON invoices.id = refunds.invoice_id
LEFT JOIN accounts ON invoices.account_id = accounts.id
WHERE invoices.paid_at >= '2026-07-01 00:00:00+00'
  AND invoices.paid_at < '2026-10-01 00:00:00+00'
  AND accounts.is_test = false
  AND accounts.deleted_at IS NULL
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


### [appdb] appdb-030 (baseline_rules) - Label: `other`

**Question:** What percentage of accounts created in Q1 2025 had churned by 30 September 2026, rounded to 2 decimals?


```sql
-- Candidate SQL:
SELECT ROUND(COUNT(DISTINCT churned_accounts.id) * 100.0 / NULLIF(COUNT(DISTINCT q1_accounts.id), 0), 2) AS churn_percentage
FROM accounts q1_accounts
LEFT JOIN (
    SELECT DISTINCT a.id
    FROM accounts a
    JOIN subscriptions s ON a.id = s.account_id
    WHERE a.is_test = false
    AND a.deleted_at IS NULL
    AND s.status = 'canceled'
    AND s.cancel_reason IN ('voluntary', 'payment_failed')
    AND s.canceled_at >= '2026-07-01 00:00:00+00'
    AND s.canceled_at < '2026-10-01 00:00:00+00'
) churned_accounts ON q1_accounts.id = churned_accounts.id
WHERE q1_accounts.is_test = false
AND q1_accounts.deleted_at IS NULL
AND q1_accounts.created_at >= '2025-01-01 00:00:00+00'
AND q1_accounts.created_at < '2025-04-01 00:00:00+00'
```

```sql
-- Gold SQL:
SELECT ROUND(100.0 * COUNT(DISTINCT s.account_id) / (
  SELECT COUNT(*) FROM accounts
   WHERE is_test = false AND deleted_at IS NULL
     AND created_at >= '2025-01-01 00:00:00+00' AND created_at < '2025-04-01 00:00:00+00'), 2)
FROM subscriptions s JOIN accounts a ON a.id = s.account_id
WHERE s.status = 'canceled' AND s.cancel_reason IN ('voluntary', 'payment_failed')
  AND s.canceled_at < '2026-10-01 00:00:00+00'
  AND a.is_test = false AND a.deleted_at IS NULL
  AND a.created_at >= '2025-01-01 00:00:00+00' AND a.created_at < '2025-04-01 00:00:00+00'
```


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


### [olist] olist-006 (baseline_rules) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(payment_value) AS avg_payment_value_per_delivered_order
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


### [olist] olist-006 (ktx) - Label: `other`

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


### [olist] olist-006 (schema_only) - Label: `other`

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


### [olist] olist-006 (wren) - Label: `other`

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


### [olist] olist-008 (datus) - Label: `other`

**Question:** Of all delivered orders, what percentage included at least one credit card payment?


```sql
-- Candidate SQL:
SELECT
    ROUND(
        (SELECT COUNT(DISTINCT o.order_id)
         FROM orders o
         JOIN order_payments op ON o.order_id = op.order_id
         WHERE o.order_status = 'delivered'
         AND op.payment_type = 'credit_card') * 100.0 /
        (SELECT COUNT(DISTINCT order_id)
         FROM orders
         WHERE order_status = 'delivered'),
        2
    ) AS percentage_of_delivered_orders_with_credit_card_payment
```

```sql
-- Gold SQL:
SELECT ROUND(100.0 * COUNT(DISTINCT p.order_id) /
       (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'), 2)
FROM order_payments p JOIN orders o ON o.order_id = p.order_id
WHERE o.order_status = 'delivered' AND p.payment_type = 'credit_card'
```

