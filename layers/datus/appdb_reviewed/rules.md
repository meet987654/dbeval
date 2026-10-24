# Business Rules for appdb

1. Real account: is_test = false AND deleted_at IS NULL. Never count test or deleted accounts.
2. Real user: users.deleted_at IS NULL AND belongs to a real account.
3. Current plan: accounts.plan_tier (starter, growth, scale). plan is old signup name, never correct for reporting.
4. Money: stored in cents. USD value = amount_cents::numeric / 100 * fx_rates.usd_per_unit using invoice currency (USD, EUR, INR). Divide as numeric.
5. Gross revenue: paid invoices (status = 'paid') with paid_at in period, real accounts only, in USD.
6. Refunds: refunds with created_at in period, real accounts only, in USD. Belongs to invoice via refunds.invoice_id (no FK).
7. Net revenue = gross revenue minus refunds for the same period (cash basis). Compute gross and refunds as two separate sums with separate date filters (paid_at for invoices, created_at for refunds), then subtract.
8. Active subscription: status = 'active' on a real account. trialing and past_due are not active.
9. Churn: status = 'canceled' AND cancel_reason IN ('voluntary', 'payment_failed'), canceled_at in period, on a real account. cancel_reason = 'upgrade' is NOT churn.
10. Active user: real user with at least one event in period.
11. Paying customer: real account with at least one paid invoice (status = 'paid') with paid_at in period.
12. ARPA: net revenue in period / paying customers in period.
13. Churned account: real account with at least one churn subscription canceled on or before date.
14. Date windows are half-open: >= start AND < next_start. Never use BETWEEN.
