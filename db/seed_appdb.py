"""Build the synthetic SaaS database `appdb` for dbeval.

Run:  python db/seed_appdb.py
Needs: pip install sqlalchemy psycopg2-binary python-dotenv
(psycopg 3 also works; the script uses whichever is installed)

The data is deterministic (fixed random seed) and ends on 2026-09-30.
Always write questions with explicit dates ("in Q3 2026"), never "last month".

THE TRAPS (this list is for you, not for the tools; do NOT add it as
COMMENT ON statements in the database, or you would be helping the tools):

 1. accounts.is_test = true marks internal test accounts. Some of them have
    normal-looking names, so a filter on the name is wrong.
 2. Soft deletes: accounts.deleted_at and users.deleted_at. Deleted rows must
    be excluded from almost every business metric.
 3. accounts.plan is the OLD plan name given at signup and never updated.
    accounts.plan_tier is the CURRENT tier. Only plan_tier is correct.
 4. Money is stored as integer cents (amount_cents) with a currency column.
    Revenue in USD needs the fx_rates table.
 5. Net revenue = paid invoices minus refunds, excluding test and deleted
    accounts, converted to USD.
 6. Churn = a subscription canceled with cancel_reason in
    ('voluntary', 'payment_failed'). cancel_reason = 'upgrade' is NOT churn,
    and an account being deleted is NOT churn.
 7. Some accounts have two subscriptions (an upgrade): the first is canceled
    with reason 'upgrade', the second is active.
 8. Foreign keys exist on subscriptions and invoices, but NOT on refunds or
    events, so a tool has to infer those joins.
 9. Active user = a non-deleted user with at least one event in the period.
"""

import os
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

ADMIN_URL = os.getenv(
    "APPDB_ADMIN_URL", "postgresql://postgres:postgres@localhost:5433/appdb"
)
UTC = timezone.utc
AS_OF = datetime(2026, 9, 30, 23, 59, 59, tzinfo=UTC)
START = datetime(2024, 1, 1, tzinfo=UTC)

N_ACCOUNTS = 2000
TIER_PRICE_USD_CENTS = {"starter": 2900, "growth": 9900, "scale": 29900}
FX = {"USD": 1.0, "EUR": 1.08, "INR": 0.012}  # usd per 1 unit of currency
OLD_PLAN_NAME = {"starter": "basic", "growth": "pro", "scale": "enterprise"}

DDL = """
DROP TABLE IF EXISTS events, refunds, invoices, subscriptions, users,
                     accounts, fx_rates CASCADE;

CREATE TABLE accounts (
    id          integer PRIMARY KEY,
    name        text NOT NULL,
    plan        text,
    plan_tier   text,
    is_test     boolean NOT NULL DEFAULT false,
    country     text,
    currency    text,
    created_at  timestamptz NOT NULL,
    deleted_at  timestamptz
);

CREATE TABLE users (
    id          integer PRIMARY KEY,
    account_id  integer NOT NULL,
    email       text,
    role        text,
    created_at  timestamptz NOT NULL,
    deleted_at  timestamptz
);

CREATE TABLE subscriptions (
    id            integer PRIMARY KEY,
    account_id    integer NOT NULL REFERENCES accounts(id),
    plan_tier     text NOT NULL,
    status        text NOT NULL,
    started_at    timestamptz NOT NULL,
    trial_ends_at timestamptz,
    canceled_at   timestamptz,
    cancel_reason text
);

CREATE TABLE invoices (
    id              integer PRIMARY KEY,
    subscription_id integer NOT NULL REFERENCES subscriptions(id),
    account_id      integer NOT NULL REFERENCES accounts(id),
    amount_cents    integer NOT NULL,
    currency        text NOT NULL,
    status          text NOT NULL,
    issued_at       timestamptz NOT NULL,
    paid_at         timestamptz
);

CREATE TABLE refunds (
    id            integer PRIMARY KEY,
    invoice_id    integer NOT NULL,
    amount_cents  integer NOT NULL,
    created_at    timestamptz NOT NULL
);

CREATE TABLE events (
    id          integer PRIMARY KEY,
    account_id  integer NOT NULL,
    user_id     integer NOT NULL,
    event_type  text NOT NULL,
    occurred_at timestamptz NOT NULL
);

CREATE TABLE fx_rates (
    currency     text PRIMARY KEY,
    usd_per_unit numeric(10, 5) NOT NULL
);
"""


def make_engine(url):
    """Pick whichever Postgres driver is installed (psycopg2 or psycopg 3)."""
    if url.startswith("postgresql://"):
        try:
            import psycopg2  # noqa: F401

            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        except ImportError:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url)


def rand_dt(rng, lo, hi):
    span = int((hi - lo).total_seconds())
    return lo + timedelta(seconds=rng.randint(0, max(span, 1)))


def add_months(dt, n):
    month = dt.month - 1 + n
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, 28)
    return dt.replace(year=year, month=month, day=day)


def build_data(rng):
    accounts, users, subs, invoices, refunds, events = [], [], [], [], [], []
    sub_id = inv_id = ref_id = ev_id = user_id = 0

    countries = [("US", "USD"), ("DE", "EUR"), ("FR", "EUR"), ("IN", "INR"), ("GB", "USD")]
    country_weights = [55, 12, 8, 10, 15]
    tiers = ["starter", "growth", "scale"]
    tier_weights = [60, 30, 10]
    words = ["Acme", "Blue", "Nimbus", "Orbit", "Pixel", "Quark", "Raven", "Solar", "Tango", "Umbra"]
    nouns = ["Labs", "Systems", "Works", "Group", "Studio", "Cloud", "Ops", "Data"]

    for acc_id in range(1, N_ACCOUNTS + 1):
        created = rand_dt(rng, START, AS_OF - timedelta(days=20))
        country, currency = rng.choices(countries, weights=country_weights)[0]
        final_tier = rng.choices(tiers, weights=tier_weights)[0]

        # Upgrade story: 12 percent of accounts start one tier lower.
        upgraded = final_tier != "starter" and rng.random() < 0.12 and (AS_OF - created).days > 90
        signup_tier = tiers[tiers.index(final_tier) - 1] if upgraded else final_tier

        is_test = rng.random() < 0.05
        name = f"{rng.choice(words)} {rng.choice(nouns)} {acc_id}"
        if is_test and rng.random() < 0.5:
            name = f"Test Account {acc_id}"  # only half of the test accounts look like tests

        deleted_at = None
        if rng.random() < 0.08:
            deleted_at = rand_dt(rng, created + timedelta(days=30), AS_OF)

        accounts.append(
            dict(
                id=acc_id, name=name, plan=OLD_PLAN_NAME[signup_tier], plan_tier=final_tier,
                is_test=is_test, country=country, currency=currency,
                created_at=created, deleted_at=deleted_at,
            )
        )

        # users
        acc_users = []
        for _ in range(rng.randint(1, 6)):
            user_id += 1
            u_created = created + timedelta(days=rng.randint(0, 40))
            u_deleted = rand_dt(rng, u_created, AS_OF) if rng.random() < 0.03 else None
            users.append(
                dict(
                    id=user_id, account_id=acc_id, email=f"user{user_id}@example.com",
                    role=rng.choice(["admin", "member", "member", "viewer"]),
                    created_at=min(u_created, AS_OF), deleted_at=u_deleted,
                )
            )
            acc_users.append(user_id)

        # subscriptions: either one, or an upgrade pair
        plan_chain = []
        if upgraded:
            switch = created + timedelta(days=rng.randint(45, max(46, (AS_OF - created).days - 5)))
            plan_chain.append((signup_tier, created, switch, "upgrade"))
            plan_chain.append((final_tier, switch, None, None))
        else:
            plan_chain.append((final_tier, created, None, None))

        for tier, started, ended, reason in plan_chain:
            sub_id += 1
            trial_end = started + timedelta(days=14)
            canceled_at, cancel_reason = ended, reason
            if ended is None and rng.random() < 0.28:  # churn
                canceled_at = rand_dt(rng, started + timedelta(days=20), AS_OF)
                cancel_reason = rng.choices(["voluntary", "payment_failed"], weights=[65, 35])[0]
            if deleted_at is not None and canceled_at is None:
                canceled_at = deleted_at  # deleting an account also stops billing
                cancel_reason = "voluntary"

            if canceled_at is not None and canceled_at <= AS_OF:
                status = "canceled"
            elif trial_end > AS_OF:
                status = "trialing"
            elif rng.random() < 0.04:
                status = "past_due"
            else:
                status = "active"

            subs.append(
                dict(
                    id=sub_id, account_id=acc_id, plan_tier=tier, status=status,
                    started_at=started, trial_ends_at=trial_end,
                    canceled_at=canceled_at if status == "canceled" else None,
                    cancel_reason=cancel_reason if status == "canceled" else None,
                )
            )

            # monthly invoices after the trial
            billing_start = trial_end
            end_billing = min(canceled_at or AS_OF, AS_OF)
            month = 0
            while True:
                issued = add_months(billing_start, month)
                if issued > end_billing:
                    break
                month += 1
                inv_id += 1
                price_local = round(TIER_PRICE_USD_CENTS[tier] / FX[currency])
                roll = rng.random()
                if (AS_OF - issued).days < 7:
                    status_i = "open"
                elif roll < 0.03:
                    status_i = "failed"
                elif roll < 0.04:
                    status_i = "void"
                else:
                    status_i = "paid"
                paid_at = issued + timedelta(days=rng.randint(0, 3)) if status_i == "paid" else None
                invoices.append(
                    dict(
                        id=inv_id, subscription_id=sub_id, account_id=acc_id,
                        amount_cents=price_local, currency=currency, status=status_i,
                        issued_at=issued, paid_at=paid_at,
                    )
                )
                if status_i == "paid" and rng.random() < 0.04:
                    ref_id += 1
                    full = rng.random() < 0.5
                    refunds.append(
                        dict(
                            id=ref_id, invoice_id=inv_id,
                            amount_cents=price_local if full else price_local // 2,
                            created_at=min(paid_at + timedelta(days=rng.randint(1, 20)), AS_OF),
                        )
                    )

        # events
        last_active = min(deleted_at or AS_OF, canceled_at or AS_OF)
        for uid in acc_users:
            for _ in range(rng.randint(0, 25)):
                ev_id += 1
                events.append(
                    dict(
                        id=ev_id, account_id=acc_id, user_id=uid,
                        event_type=rng.choice(["login", "login", "report_viewed", "export", "invite_sent"]),
                        occurred_at=rand_dt(rng, created, max(last_active, created + timedelta(days=1))),
                    )
                )

    return accounts, users, subs, invoices, refunds, events


def insert(conn, table, rows):
    if not rows:
        return
    cols = list(rows[0].keys())
    stmt = text(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})"
    )
    for i in range(0, len(rows), 5000):
        conn.execute(stmt, rows[i : i + 5000])


def main():
    rng = random.Random(42)
    accounts, users, subs, invoices, refunds, events = build_data(rng)

    engine = make_engine(ADMIN_URL)
    with engine.begin() as conn:
        conn.execute(text(DDL))
        for cur, rate in FX.items():
            conn.execute(
                text("INSERT INTO fx_rates VALUES (:c, :r)"), {"c": cur, "r": rate}
            )
        insert(conn, "accounts", accounts)
        insert(conn, "users", users)
        insert(conn, "subscriptions", subs)
        insert(conn, "invoices", invoices)
        insert(conn, "refunds", refunds)
        insert(conn, "events", events)
        conn.execute(text("GRANT USAGE ON SCHEMA public TO reader"))
        conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader"))

    print("appdb seeded:")
    for name, rows in [("accounts", accounts), ("users", users), ("subscriptions", subs),
                       ("invoices", invoices), ("refunds", refunds), ("events", events)]:
        print(f"  {name:14s} {len(rows):>7d}")


if __name__ == "__main__":
    main()
