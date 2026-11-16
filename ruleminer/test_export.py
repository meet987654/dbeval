"""Tests for ruleminer/export.py (dbt MetricFlow and Wren MDL export) and the `export` CLI subcommand."""

import json
import os
import re
import sqlite3
import sys
import tempfile
import unittest

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "db"))

from ruleminer.cli import main as cli_main
from ruleminer.export import export_files, filter_rules, parse_join, predicate_columns, to_dbt, to_wren
from ruleminer.synthesizer import SynthesizedRule as R

RULES = [
    R("entity_filter", "accounts", "Real accounts", "accounts.deleted_at IS NULL AND accounts.is_test = FALSE", 0.95, "mined"),
    R("entity_filter", "users", "Real users", "users.deleted_at IS NULL", 0.6, "schema"),
    R("relationship", "accounts", "join", "accounts.id = subscriptions.account_id", 0.8, "query_mining"),
    R("relationship", "events", "join", "events.user_id = users.id", 0.88, "query_mining"),
    R("currency_scale", "invoices", "cents", "invoices.amount_cents::numeric / 100", 1.0, "corroborated"),
    R("lifecycle_state", "subscriptions", "states", "subscriptions.status IN ('active', 'canceled')", 0.85, "query_mining"),
]


class TestParsing(unittest.TestCase):
    def test_parse_join_puts_id_side_first(self):
        self.assertEqual(parse_join("accounts.id = subscriptions.account_id"), ("accounts", "id", "subscriptions", "account_id"))
        self.assertEqual(parse_join("events.user_id = users.id"), ("users", "id", "events", "user_id"))
        self.assertEqual(parse_join("fx_rates.currency = invoices.currency"), ("fx_rates", "currency", "invoices", "currency"))

    def test_parse_join_rejects_non_joins(self):
        self.assertIsNone(parse_join("status = 'paid'"))
        self.assertIsNone(parse_join("not valid sql ((("))

    def test_predicate_columns(self):
        self.assertEqual(predicate_columns("accounts.deleted_at IS NULL AND is_test = FALSE", "accounts"),
                         [("accounts", "deleted_at"), ("accounts", "is_test")])


class TestFilter(unittest.TestCase):
    def test_min_confidence(self):
        self.assertEqual(len(filter_rules(RULES, 0.0)), 6)
        kept = filter_rules(RULES, 0.9)
        self.assertEqual({r.category for r in kept}, {"entity_filter", "currency_scale"})
        self.assertEqual(filter_rules(RULES, 1.1), [])


class TestDbt(unittest.TestCase):
    def setUp(self):
        self.spec = to_dbt(RULES)
        self.models = {m["name"]: m for m in self.spec["semantic_models"]}

    def test_metrics_reference_existing_measures_and_entities(self):
        measures = {m["name"] for sm in self.spec["semantic_models"] for m in sm["measures"]}
        entities = {e["name"] for sm in self.spec["semantic_models"] for e in sm["entities"]}
        self.assertEqual({m["name"] for m in self.spec["metrics"]}, {"real_accounts", "real_users"})
        for m in self.spec["metrics"]:
            self.assertIn(m["type_params"]["measure"], measures)
            for ent, dim in re.findall(r"Dimension\('(\w+?)__(\w+)'\)", m["filter"]):
                self.assertIn(ent, entities)

    def test_filter_uses_primary_entity_of_table(self):
        real_accounts = next(m for m in self.spec["metrics"] if m["name"] == "real_accounts")
        self.assertEqual(
            real_accounts["filter"],
            "{{ Dimension('accounts_id__deleted_at') }} IS NULL AND {{ Dimension('accounts_id__is_test') }} = FALSE",
        )
        self.assertEqual(real_accounts["meta"]["ruleminer"], {"confidence": 0.95, "source": "mined"})

    def test_relationship_becomes_primary_and_foreign_entities(self):
        self.assertIn(("accounts_id", "primary"), [(e["name"], e["type"]) for e in self.models["accounts"]["entities"]])
        self.assertIn(("accounts_id", "foreign"), [(e["name"], e["type"]) for e in self.models["subscriptions"]["entities"]])
        for sm in self.spec["semantic_models"]:
            self.assertEqual(sum(e["type"] == "primary" for e in sm["entities"]), 1, sm["name"])

    def test_money_scale_measure_and_status_note(self):
        m = next(x for x in self.models["invoices"]["measures"] if x["name"] == "amount_cents_sum_scaled")
        self.assertEqual(m["expr"], "amount_cents::numeric / 100")
        self.assertNotIn("amount_cents", [d["name"] for d in self.models["invoices"]["dimensions"]])
        status = next(d for d in self.models["subscriptions"]["dimensions"] if d["name"] == "status")
        self.assertEqual(status["description"], "states")

    def test_min_confidence_drops_metrics(self):
        spec = to_dbt(RULES, min_confidence=0.9)
        self.assertEqual([m["name"] for m in spec["metrics"]], ["real_accounts"])

    def test_yaml_roundtrip(self):
        text = export_files("dbt", RULES)["ruleminer_semantic_models.yml"]
        self.assertEqual(yaml.safe_load(text), self.spec)


class TestWren(unittest.TestCase):
    def setUp(self):
        self.mdl = to_wren(RULES)

    def test_relationships_reference_models(self):
        names = {m["name"] for m in self.mdl["models"]}
        self.assertEqual(len(self.mdl["relationships"]), 2)
        for rel in self.mdl["relationships"]:
            self.assertTrue(set(rel["models"]) <= names)
            self.assertEqual(rel["joinType"], "MANY_TO_ONE")
        rel = next(r for r in self.mdl["relationships"] if r["models"][0] == "subscriptions")
        self.assertEqual(rel["condition"], "subscriptions.account_id = accounts.id")

    def test_primary_keys_and_calculated_column(self):
        accounts = next(m for m in self.mdl["models"] if m["name"] == "accounts")
        self.assertEqual(accounts["primaryKey"], "id")
        inv = next(m for m in self.mdl["models"] if m["name"] == "invoices")
        calc = next(c for c in inv["columns"] if c["isCalculated"])
        self.assertEqual((calc["name"], calc["expression"]), ("amount_units", "CAST(amount_cents AS DECIMAL) / 100"))

    def test_entity_filter_becomes_unqualified_view(self):
        views = {v["name"]: v for v in self.mdl["views"]}
        self.assertEqual(views["real_accounts"]["statement"], "SELECT * FROM accounts WHERE deleted_at IS NULL AND is_test = FALSE")
        self.assertEqual(views["real_accounts"]["properties"]["ruleminer_confidence"], "0.95")

    def test_schema_types_win_and_are_normalized(self):
        mdl = to_wren(RULES, schema={"accounts": {"deleted_at": "TIMESTAMP WITH TIME ZONE", "id": "INTEGER", "is_test": "BOOLEAN"}})
        cols = {c["name"]: c["type"] for c in next(m for m in mdl["models"] if m["name"] == "accounts")["columns"]}
        self.assertEqual(cols["deleted_at"], "TIMESTAMPTZ")

    def test_guessed_types_without_schema(self):
        cols = {c["name"]: c["type"] for c in next(m for m in self.mdl["models"] if m["name"] == "accounts")["columns"]}
        self.assertEqual(cols, {"deleted_at": "TIMESTAMP", "id": "INTEGER", "is_test": "BOOLEAN"})

    def test_min_confidence_filters_views(self):
        self.assertEqual([v["name"] for v in to_wren(RULES, min_confidence=0.9)["views"]], ["real_accounts"])

    def test_unknown_format(self):
        with self.assertRaises(ValueError):
            export_files("lookml", RULES)


class TestCli(unittest.TestCase):
    def test_export_subcommand_end_to_end(self):
        import seed_appdb as s

        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "appdb.sqlite")
            con = sqlite3.connect(db_path)
            con.executescript(s.SQLITE_DDL)
            con.commit()
            con.close()
            url = f"sqlite:///{db_path}"

            out_dbt = os.path.join(tmp, "dbt_models")
            self.assertEqual(cli_main(["export", "--format", "dbt", "--out", out_dbt, "--url", url]), 0)
            with open(os.path.join(out_dbt, "ruleminer_semantic_models.yml"), encoding="utf-8") as f:
                spec = yaml.safe_load(f)
            self.assertTrue(any(m["name"] == "real_accounts" for m in spec["metrics"]))

            out_wren = os.path.join(tmp, "wren_models")
            self.assertEqual(cli_main(["export", "--format", "wren", "--out", out_wren, "--url", url, "--min-confidence", "0.9"]), 0)
            with open(os.path.join(out_wren, "manifest.json"), encoding="utf-8") as f:
                mdl = json.load(f)
            self.assertIn("accounts", {m["name"] for m in mdl["models"]})
            self.assertTrue(all(float(v["properties"]["ruleminer_confidence"]) >= 0.9 for v in mdl["views"]))


if __name__ == "__main__":
    unittest.main()
