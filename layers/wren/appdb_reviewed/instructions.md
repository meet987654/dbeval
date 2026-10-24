# Business Rules & Guidelines for Query Generation

1. **Real account**: `is_test = false AND deleted_at IS NULL`. Never count test or deleted accounts in any business metric. Use the `real_accounts` view when available.
2. **Real user**: `users.deleted_at IS NULL` and belongs to a real account (`accounts.is_test = false AND accounts.deleted_at IS NULL`). Use the `real_users` view when available.
3. **Current plan**: `accounts.plan_tier`. The `plan` column is the old name from signup and is never correct for reporting.
4. **Money / USD conversion**: Stored in cents. USD value = `amount_cents::numeric / 100 * fx_rates.usd_per_unit`, using the currency of the invoice (a refund uses the currency of its invoice). Always divide as numeric (`amount_cents::numeric / 100`) to avoid integer truncation.
5. **Gross revenue**: For a period: paid invoices (`status = 'paid'`) with `paid_at` in the period, real accounts only, in USD: `SUM(amount_cents::numeric / 100 * fx_rates.usd_per_unit)`. Use `paid_invoices` view.
6. **Refunds**: For a period: refunds with `created_at` in the period, real accounts only, in USD. A refund belongs to an invoice through `refunds.invoice_id = invoices.id`.
7. **Net revenue**: Gross revenue minus refunds for the same period (cash basis). Compute gross and refunds as two separate subqueries (invoices filtered on `paid_at`, refunds filtered on `created_at`), then subtract. Do not join invoices to refunds in one filtered query.
8. **Active subscription**: `status = 'active'` on a real account. `trialing` and `past_due` are NOT active. Use `active_subscriptions` view.
9. **Churn**: A subscription with `status = 'canceled'` and `cancel_reason IN ('voluntary', 'payment_failed')`, `canceled_at` in the period, on a real account. `cancel_reason = 'upgrade'` is NOT churn. Use `churn_subscriptions` view.
10. **Active user**: In a period: a real user with at least one event in `events` where `occurred_at` is in the period.
11. **Paying customer**: In a period: a real account with at least one paid invoice (`status = 'paid'`) whose `paid_at` is in the period.
12. **ARPA**: Average revenue per paying customer = Net revenue in the period divided by the number of paying customers in the period.
13. **Churned account**: A real account that has at least one churn subscription canceled on or before the date asked about.
14. **Date windows**: Always half-open: `>= start AND < next_period_start`. E.g., Q3 2026 is `>= '2026-07-01 00:00:00+00' AND < '2026-10-01 00:00:00+00'`. Never use `BETWEEN` with an end date.
