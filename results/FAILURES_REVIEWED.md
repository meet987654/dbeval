# dbeval Failure Attribution Report

Source: `results/raw/suite_results_all.csv`

Failures are categorized by automated comparison of candidate SQL against the gold SQL rule requirements and PostgreSQL engine errors.


## Database: appdb

| Failure Label | baseline | baseline_rules | datus | datus_reviewed | datus_reviewed_defonly | ktx | ktx_reviewed | schema_only | schema_true_joins | wren | wren_reviewed | wren_reviewed_unresolved |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `missing:cancel_reason+soft_delete` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |
| `missing:cancel_reason+soft_delete+test_filter` | 4 | 0 | 4 | 0 | 0 | 4 | 0 | 3 | 3 | 3 | 0 | 0 |
| `missing:cents_conversion+paid_invoice_filter+soft_delete+test_filter` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `missing:cents_conversion+refund_netting+soft_delete+test_filter` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `missing:cents_conversion+soft_delete+test_filter` | 1 | 0 | 2 | 0 | 0 | 2 | 0 | 1 | 2 | 1 | 0 | 0 |
| `missing:fx_join+soft_delete+test_filter` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| `missing:paid_invoice_filter+soft_delete+test_filter` | 0 | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 |
| `missing:plan_tier+soft_delete` | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `missing:plan_tier+soft_delete+test_filter` | 2 | 0 | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 2 | 0 | 0 |
| `missing:plan_tier+test_filter` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `missing:refund_netting` | 0 | 0 | 0 | 2 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 1 |
| `missing:refund_netting+soft_delete` | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| `missing:refund_netting+soft_delete+test_filter` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `missing:soft_delete` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| `missing:soft_delete+test_filter` | 17 | 1 | 14 | 3 | 2 | 16 | 1 | 17 | 16 | 14 | 1 | 1 |
| `missing:test_filter` | 1 | 0 | 2 | 0 | 0 | 1 | 0 | 2 | 3 | 1 | 0 | 0 |
| `other` | 0 | 3 | 0 | 0 | 2 | 0 | 3 | 0 | 0 | 0 | 1 | 2 |
| `sql_error:grouping_error` | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 0 | 0 |
| `sql_error:runtime_error` | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `sql_error:undefined_function` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 3 |
| **TOTAL FAILURES** | 28 | 5 | 27 | 6 | 6 | 28 | 6 | 29 | 28 | 28 | 3 | 7 |


## Database: olist

| Failure Label | baseline | baseline_rules | datus | datus_reviewed | datus_reviewed_defonly | ktx | ktx_reviewed | schema_only | schema_true_joins | wren | wren_reviewed | wren_reviewed_unresolved |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `missing:customer_unique_id` | 3 | 0 | 1 | 0 | 0 | 1 | 1 | 3 | 3 | 1 | 1 | 1 |
| `missing:date_cast+sales_status_filter` | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| `missing:sales_status_filter` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 |
| `other` | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 1 | 1 |
| `sql_error:runtime_error` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| `sql_error:syntax_error` | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 1 |
| `sql_error:undefined_function` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| **TOTAL FAILURES** | 5 | 3 | 6 | 2 | 3 | 4 | 3 | 7 | 6 | 5 | 4 | 4 |


## Detailed Inspection: `other` and `baseline_rules` Failures

Below are questions where `failure_label` is `other` or where `baseline_rules` failed:


### [appdb] appdb-008 (datus_reviewed_defonly) - Label: `other`

**Question:** What was our net revenue in USD in Q3 2026?


```sql
-- Candidate SQL:
SELECT
    SUM(CASE WHEN invoices.status = 'paid' THEN (invoices.amount_cents::numeric / 100) * fx_rates.usd_per_unit ELSE 0 END) -
    SUM(CASE WHEN refunds.id IS NOT NULL THEN (refunds.amount_cents::numeric / 100) * fx_rates.usd_per_unit ELSE 0 END) AS net_revenue
FROM
    accounts
JOIN
    invoices ON accounts.id = invoices.account_id
LEFT JOIN
    fx_rates ON invoices.currency = fx_rates.currency
LEFT JOIN
    refunds ON invoices.id = refunds.invoice_id
WHERE
    accounts.is_test = false
    AND accounts.deleted_at IS NULL
    AND (
        (invoices.status = 'paid' AND invoices.paid_at >= '2026-07-01' AND invoices.paid_at < '2026-10-01')
        OR
        (refunds.id IS NOT NULL AND refunds.created_at >= '2026-07-01' AND refunds.created_at < '2026-10-01')
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


### [appdb] appdb-008 (ktx_reviewed) - Label: `other`

**Question:** What was our net revenue in USD in Q3 2026?


```sql
-- Candidate SQL:
SELECT
  SUM(CASE WHEN invoices.status = 'paid' AND accounts.is_test = false AND accounts.deleted_at IS NULL AND invoices.paid_at >= '2026-07-01' AND invoices.paid_at < '2026-10-01' THEN invoices.amount_cents::numeric / 100 * fx_rates.usd_per_unit ELSE 0 END) -
  SUM(CASE WHEN accounts.is_test = false AND accounts.deleted_at IS NULL AND refunds.created_at >= '2026-07-01' AND refunds.created_at < '2026-10-01' THEN refunds.amount_cents::numeric / 100 * fx_rates.usd_per_unit ELSE 0 END) AS net_revenue_usd
FROM
  invoices
JOIN
  accounts ON invoices.account_id = accounts.id
JOIN
  fx_rates ON invoices.currency = fx_rates.currency
LEFT JOIN
  refunds ON invoices.id = refunds.invoice_id
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


### [appdb] appdb-020 (datus_reviewed_defonly) - Label: `other`

**Question:** How many accounts paid us more than 2000 USD in 2026 after refunds?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT a.id) AS accounts_paid_more_than_2000_usd
FROM accounts a
JOIN invoices i ON a.id = i.account_id
JOIN fx_rates f ON a.currency = f.currency
WHERE a.is_test = false
  AND a.deleted_at IS NULL
  AND i.status = 'paid'
  AND i.paid_at >= '2026-01-01'
  AND i.paid_at < '2027-01-01'
GROUP BY a.id
HAVING SUM(i.amount_cents::numeric / 100 * f.usd_per_unit) > 2000
  AND SUM(i.amount_cents::numeric / 100 * f.usd_per_unit) - (
      SELECT COALESCE(SUM(r.amount_cents::numeric / 100 * f2.usd_per_unit), 0)
      FROM refunds r
      JOIN invoices i2 ON r.invoice_id = i2.id
      JOIN fx_rates f2 ON i2.currency = f2.currency
      WHERE i2.account_id = a.id
        AND r.created_at >= '2026-01-01'
        AND r.created_at < '2027-01-01'
  ) > 2000
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


### [appdb] appdb-020 (wren_reviewed) - Label: `other`

**Question:** How many accounts paid us more than 2000 USD in 2026 after refunds?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT a.id) AS account_count
FROM accounts a
JOIN invoices i ON a.id = i.account_id
JOIN fx_rates f ON i.currency = f.currency
LEFT JOIN refunds r ON i.id = r.invoice_id
WHERE a.is_test = false
  AND a.deleted_at IS NULL
  AND i.status = 'paid'
  AND i.paid_at >= '2026-01-01'
  AND i.paid_at < '2027-01-01'
GROUP BY a.id
HAVING SUM((i.amount_cents::numeric / 100) * f.usd_per_unit) - COALESCE(SUM((r.amount_cents::numeric / 100) * f.usd_per_unit), 0) > 2000
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


### [appdb] appdb-020 (wren_reviewed_unresolved) - Label: `other`

**Question:** How many accounts paid us more than 2000 USD in 2026 after refunds?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT a.id) AS account_count
FROM accounts a
JOIN invoices i ON a.id = i.account_id
JOIN fx_rates f ON i.currency = f.currency
LEFT JOIN refunds r ON i.id = r.invoice_id
WHERE a.is_test = false
  AND a.deleted_at IS NULL
  AND i.status = 'paid'
  AND i.paid_at >= '2026-01-01'
  AND i.paid_at < '2027-01-01'
GROUP BY a.id
HAVING SUM((i.amount_cents::numeric / 100) * f.usd_per_unit) - COALESCE(SUM((r.amount_cents::numeric / 100) * f.usd_per_unit), 0) > 2000
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


### [appdb] appdb-022 (wren_reviewed_unresolved) - Label: `other`

**Question:** How many customers are on a growth plan but have never been billed a paid invoice?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT a.id) AS growth_customers_without_paid_invoices
FROM accounts a
JOIN subscriptions s ON a.id = s.account_id
LEFT JOIN invoices i ON a.id = i.account_id AND i.status = 'paid'
WHERE a.is_test = false
  AND a.deleted_at IS NULL
  AND s.plan_tier = 'growth'
  AND i.id IS NULL
```

```sql
-- Gold SQL:
SELECT COUNT(*) FROM accounts a
WHERE a.plan_tier = 'growth' AND a.is_test = false AND a.deleted_at IS NULL
  AND NOT EXISTS (SELECT 1 FROM invoices i WHERE i.account_id = a.id AND i.status = 'paid')
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


### [appdb] appdb-030 (ktx_reviewed) - Label: `other`

**Question:** What percentage of accounts created in Q1 2025 had churned by 30 September 2026, rounded to 2 decimals?


```sql
-- Candidate SQL:
SELECT ROUND(COUNT(DISTINCT CASE WHEN accounts.is_test = false AND accounts.deleted_at IS NULL AND subscriptions.status = 'canceled' AND subscriptions.cancel_reason IN ('voluntary', 'payment_failed') AND subscriptions.canceled_at <= '2026-09-30' THEN accounts.id END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN accounts.is_test = false AND accounts.deleted_at IS NULL AND accounts.created_at >= '2025-01-01' AND accounts.created_at < '2025-04-01' THEN accounts.id END), 0), 2) AS churn_percentage
FROM accounts
LEFT JOIN subscriptions ON accounts.id = subscriptions.account_id
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


### [appdb] appdb-031 (ktx_reviewed) - Label: `other`

**Question:** How many distinct users logged in at least once in Q3 2026?


```sql
-- Candidate SQL:
SELECT COUNT(DISTINCT users.id)
FROM users
JOIN accounts ON users.account_id = accounts.id
JOIN events ON users.id = events.user_id
WHERE users.deleted_at IS NULL
AND accounts.is_test = false
AND accounts.deleted_at IS NULL
AND events.event_type = 'login'
AND events.occurred_at >= '2026-07-01'
AND events.occurred_at < '2026-10-01'
```

```sql
-- Gold SQL:
SELECT COUNT(DISTINCT e.user_id) FROM events e
JOIN users u ON u.id = e.user_id JOIN accounts a ON a.id = u.account_id
WHERE e.event_type = 'login'
  AND e.occurred_at >= '2026-07-01 00:00:00+00' AND e.occurred_at < '2026-10-01 00:00:00+00'
  AND u.deleted_at IS NULL AND a.is_test = false AND a.deleted_at IS NULL
```


### [olist] olist-005 (ktx_reviewed) - Label: `other`

**Question:** What were total sales in 2017, excluding shipping costs?


```sql
-- Candidate SQL:
SELECT SUM(CASE WHEN orders.order_status NOT IN ('canceled', 'unavailable') THEN order_items.price ELSE 0 END) AS total_sales
FROM order_items
JOIN orders ON order_items.order_id = orders.order_id
WHERE orders.order_purchase_timestamp::timestamp BETWEEN '2017-01-01' AND '2017-12-31'
```

```sql
-- Gold SQL:
SELECT ROUND(SUM(oi.price::numeric), 2)
FROM order_items oi JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_status NOT IN ('canceled', 'unavailable')
  AND o.order_purchase_timestamp::timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp::timestamp < '2018-01-01'
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


### [olist] olist-006 (datus_reviewed_defonly) - Label: `other`

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


### [olist] olist-006 (ktx_reviewed) - Label: `other`

**Question:** What was the average payment value per delivered order?


```sql
-- Candidate SQL:
SELECT AVG(op.payment_value) AS avg_payment_value_per_delivered_order
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


### [olist] olist-006 (wren_reviewed) - Label: `other`

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


### [olist] olist-006 (wren_reviewed_unresolved) - Label: `other`

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


### [olist] olist-007 (datus_reviewed_defonly) - Label: `other`

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


### [olist] olist-014 (datus_reviewed) - Label: `other`

**Question:** How many products are in the catalog?


```sql
-- Candidate SQL:
SELECT COUNT(*) AS product_count
FROM olist.public.products
WHERE product_category_name IS NOT NULL
```

```sql
-- Gold SQL:
SELECT COUNT(*) FROM products
```

