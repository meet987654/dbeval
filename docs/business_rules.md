# Business rules (the "answer key" knowledge) - version 2

Version 2 clarifies three things the first version left loose: numeric division in rule 4,
separate sums in rule 7, and half-open date windows in rule 14. Version 1 is the git tag `rules-v1`.

These are the definitions behind every gold answer.

- The gold-answer generator uses them (LLM oracle prompts in `scorer/validate_gold.py`).
- On Day 5, every tool gets the SAME rules to encode in its own format during its
  30-minute review. This keeps the review fair: no tool wins because you happened
  to spot more problems in it.
- During Day 3 (out-of-the-box build) tools must NOT see this file.

All timestamps are UTC. A "quarter" is a calendar quarter.

## appdb (SaaS product)

1. **Real account**: `is_test = false` AND `deleted_at IS NULL`.
   Never count test or deleted accounts in any business metric.
2. **Real user**: `users.deleted_at IS NULL` and belongs to a real account.
3. **Current plan**: `accounts.plan_tier`. The `plan` column is the old name from
   signup and is never correct for reporting.
4. **Money**: stored in cents. USD value = `amount_cents::numeric / 100 * fx_rates.usd_per_unit`,
   using the currency of the invoice (a refund uses the currency of its invoice). Divide as
   numeric: plain integer division (`amount_cents / 100`) drops cents and gives wrong totals.
5. **Gross revenue** for a period: paid invoices (`status = 'paid'`) with `paid_at` in
   the period, real accounts only, in USD.
6. **Refunds** for a period: refunds with `created_at` in the period, real accounts
   only, in USD. A refund belongs to an invoice through `refunds.invoice_id`
   (there is no foreign key).
7. **Net revenue** = gross revenue minus refunds, for the same period (cash basis).
   Refunds count in the period they were issued, even if the invoice is older. Compute gross
   and refunds as two separate sums, each filtered on its own date column (`paid_at` for
   invoices, `created_at` for refunds), then subtract. Do not join invoices to refunds in one
   filtered query, because that mixes the two periods.
8. **Active subscription**: `status = 'active'` on a real account. `trialing`
   and `past_due` are separate states and are not "active".
9. **Churn**: a subscription with `status = 'canceled'` and
   `cancel_reason IN ('voluntary', 'payment_failed')`, `canceled_at` in the period,
   on a real account. `cancel_reason = 'upgrade'` is NOT churn.
10. **Active user** in a period: a real user with at least one event in the period.

11. **Paying customer** in a period: a real account with at least one paid invoice
    (`status = 'paid'`) whose `paid_at` is in the period.
12. **Average revenue per paying customer (ARPA)** = net revenue in the period divided by
    the number of paying customers in the period.
13. **Churned account**: a real account that has at least one churn subscription (rule 9)
    canceled on or before the date asked about.

14. **Date windows** are half-open: the start is included and the next period's start is
    excluded. Q3 2026 means `>= '2026-07-01 00:00:00+00' AND < '2026-10-01 00:00:00+00'`;
    September 2026 means `>= '2026-09-01 00:00:00+00' AND < '2026-10-01 00:00:00+00'`.
    Never use `BETWEEN` with an end date such as '2026-09-30', because it drops the last day.

## olist (Brazilian e-commerce)

1. **Customer (a person)** = `customers.customer_unique_id`. `customer_id` is
   created per order, so counting it counts orders, not people.
2. **Sales / sold** = order items on orders whose status is not `canceled` or `unavailable`.
   This applies to anything described as sales, sold or revenue (for example "items sold",
   "had a sale", "total sales"), and `order_items.price` is the sales amount (freight is NOT
   sales). Questions about who ordered, or how many orders there were, count every order
   regardless of status unless the question says otherwise.
3. **Order payment value** = the SUM of that order's rows in `order_payments`
   (one order can have several payment rows). Never join payments to items; it
   multiplies the rows.
4. **Delivered** = `order_status = 'delivered'`. **Late** = `order_delivered_customer_date`
   is after `order_estimated_delivery_date`.
5. **Delivery time** = days from `order_purchase_timestamp` to `order_delivered_customer_date`.
6. **Category** = the English name from `product_category_name_translation`. If a
   category has no translation, use the Portuguese name. Products with no category
   are ignored for category questions.
7. If an order has several reviews, use the most recent one (`review_creation_date`).
8. Date columns in this database are stored as text; cast them to timestamps first.
