## appdb (Discovered Business Rules & Schema Invariants)

> Automatically extracted by RuleMiner from database schema signals and historical query logs.

### 1. Real Entities & Exclusion Predicates
1. **Real accounts: Always filter `accounts.deleted_at IS NULL AND accounts.is_test = FALSE` to exclude deleted or test records.**
2. **Real users: Always filter `users.deleted_at IS NULL` to exclude deleted or test records.**

### 2. Monetary & Numeric Scales
3. **Money scale on `invoices.amount_cents`: Stored in cents. Always convert using numeric division: `invoices.amount_cents::numeric / 100`.**
4. **Money scale on `refunds.amount_cents`: Stored in cents. Always convert using numeric division: `refunds.amount_cents::numeric / 100`.**

### 3. Discovered Join Paths & Foreign Keys
5. **Join relationship: `accounts.id = subscriptions.account_id`.**
6. **Join relationship: `accounts.id = invoices.account_id`.**
7. **Join relationship: `fx_rates.currency = invoices.currency`.**
8. **Join relationship: `invoices.id = refunds.invoice_id`.**
9. **Join relationship: `accounts.id = users.account_id`.**
10. **Join relationship: `events.user_id = users.id`.**

### 4. Lifecycle States & Status Semantics
11. **Observed lifecycle states for `subscriptions.status`: ['active', 'canceled', 'past_due']. Filter according to question semantics (e.g. active vs canceled/paid).**
12. **Observed lifecycle states for `invoices.status`: ['failed', 'paid']. Filter according to question semantics (e.g. active vs canceled/paid).**