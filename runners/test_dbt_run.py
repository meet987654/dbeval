#!/usr/bin/env python3
"""Unit tests for runners/dbt_run.py (dbt Semantic Layer / MetricFlow adapter). No LLM or DB server needed."""

import os
import sqlite3
import sys
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "db"))

import dbt_run
import seed_appdb as s


def _table_columns():
    con = sqlite3.connect(":memory:")
    con.executescript(s.SQLITE_DDL)
    tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
    return {t: {r[1] for r in con.execute(f"pragma table_info({t})")} for t in tables}


def test_layer_structure():
    layer = dbt_run.load_layer("appdb")
    models = {m["name"]: m for m in layer["semantic_models"]}
    measures = {x["name"] for m in layer["semantic_models"] for x in m.get("measures", [])}
    metrics = {m["name"]: m for m in layer["metrics"]}
    assert {"real_accounts", "active_subscriptions", "churned_subscriptions", "net_revenue"} <= set(metrics)
    for m in metrics.values():
        tp = m["type_params"]
        if m["type"] == "simple":
            assert tp["measure"] in measures, f"{m['name']}: unknown measure {tp['measure']}"
        elif m["type"] == "derived":
            assert set(tp["metrics"]) <= set(metrics)
        elif m["type"] == "ratio":
            assert {tp["numerator"], tp["denominator"]} <= set(metrics)
    assert set(models) == {"accounts", "users", "subscriptions", "invoices", "refunds", "events"}


def test_layer_matches_database_schema():
    cols = _table_columns()
    for sm in dbt_run.load_layer("appdb")["semantic_models"]:
        table = sm["model"].replace("ref('", "").replace("')", "")
        assert table in cols, f"unknown table {table}"
        for e in sm.get("entities", []):
            col = e.get("expr", e["name"])
            if e["name"] != "currency":  # currency entity joins to fx_rates on the invoice currency column
                assert col in cols[table], f"{table}.{col}"
        for d in sm.get("dimensions", []):
            assert d["name"] in cols[table], f"{table}.{d['name']}"


def test_render_context_carries_business_rules():
    ctx = dbt_run.render_context(dbt_run.load_layer("appdb"))
    assert "DBT METRICS" in ctx
    assert "is_test') }} = false" in ctx and "deleted_at') }} IS NULL" in ctx
    assert "voluntary" in ctx and "upgrade is NOT churn" in ctx
    assert "derived: gross_revenue - refunds" in ctx
    assert "ratio: net_revenue / paying_customers" in ctx


def test_unknown_db_has_no_layer():
    try:
        dbt_run.load_layer("olist")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    r = dbt_run.answer("olist", "How many orders?")
    assert r["system"] == "dbt" and r["error"] and "No dbt semantic layer" in r["error"]


def test_answer_with_mocked_llm_and_db():
    seen = {}

    def fake_llm(system, user):
        seen["user"] = user
        return "```sql\nSELECT COUNT(*) FROM accounts WHERE is_test = false AND deleted_at IS NULL;\n```", 123, 45

    with patch.object(dbt_run.b, "call_llm", fake_llm), \
            patch.object(dbt_run.b, "schema_text", lambda db: "TABLE accounts(...)"), \
            patch.object(dbt_run.b, "run_sql", lambda db, sql: (["count"], [(7,)])):
        r = dbt_run.answer("appdb", "How many accounts do we have?")
    assert r["error"] is None, r["error"]
    assert r["rows"] == [(7,)] and r["columns"] == ["count"]
    assert (r["tokens_in"], r["tokens_out"]) == (123, 45)
    assert r["sql"].startswith("SELECT COUNT(*)")
    assert "DBT METRICS" in seen["user"] and "QUESTION\nHow many accounts do we have?" in seen["user"]


def test_answer_refuses_non_read_only_sql():
    with patch.object(dbt_run.b, "call_llm", lambda s_, u: ("DROP TABLE accounts", 1, 1)), \
            patch.object(dbt_run.b, "schema_text", lambda db: ""):
        r = dbt_run.answer("appdb", "drop it")
    assert r["error"] and "Refused" in r["error"] and r["rows"] == []


def run_all_tests():
    test_layer_structure()
    test_layer_matches_database_schema()
    test_render_context_carries_business_rules()
    test_unknown_db_has_no_layer()
    test_answer_with_mocked_llm_and_db()
    test_answer_refuses_non_read_only_sql()
    print("dbt_run.py: all unit tests passed")


if __name__ == "__main__":
    run_all_tests()
