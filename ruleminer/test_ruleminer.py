"""Unit tests for RuleMiner:
Tests schema signal heuristics, query log mining with sqlglot, rule synthesis, and runner integration.
"""

import json
import os
import tempfile
import unittest
import yaml

from ruleminer.query_log_miner import MinedPredicate, QueryLogMiner
from ruleminer.runner import get_induced_rules_text
from ruleminer.schema_signals import SchemaSignalExtractor
from ruleminer.synthesizer import RuleSynthesizer, SynthesizedRule


class TestSchemaSignalExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = SchemaSignalExtractor()
        self.sample_metadata = {
            "accounts": [
                {"name": "id", "type": "INTEGER", "nullable": False},
                {"name": "name", "type": "VARCHAR", "nullable": False},
                {"name": "is_test", "type": "BOOLEAN", "nullable": False},
                {"name": "deleted_at", "type": "TIMESTAMP", "nullable": True},
                {"name": "is_active", "type": "BOOLEAN", "nullable": False},
                {"name": "plan_tier", "type": "VARCHAR", "nullable": False},
            ],
            "invoices": [
                {"name": "id", "type": "INTEGER", "nullable": False},
                {"name": "account_id", "type": "INTEGER", "nullable": False},
                {"name": "amount_cents", "type": "INTEGER", "nullable": False},
                {"name": "status", "type": "VARCHAR", "nullable": False},
            ],
            "refunds": [
                {"name": "id", "type": "INTEGER", "nullable": False},
                {"name": "invoice_id", "type": "INTEGER", "nullable": False},
                {"name": "amount_cents", "type": "INTEGER", "nullable": False},
            ],
        }

    def test_soft_delete_detection(self):
        signals = self.extractor.extract_from_metadata(self.sample_metadata)
        soft_del = [s for s in signals if s.signal_type == "soft_delete"]
        self.assertEqual(len(soft_del), 1)
        self.assertEqual(soft_del[0].table, "accounts")
        self.assertEqual(soft_del[0].column, "deleted_at")
        self.assertEqual(soft_del[0].suggested_predicate, "accounts.deleted_at IS NULL")

    def test_test_filter_detection(self):
        signals = self.extractor.extract_from_metadata(self.sample_metadata)
        test_sigs = [s for s in signals if s.signal_type == "test_filter"]
        self.assertEqual(len(test_sigs), 1)
        self.assertEqual(test_sigs[0].table, "accounts")
        self.assertEqual(test_sigs[0].column, "is_test")
        self.assertEqual(test_sigs[0].suggested_predicate, "accounts.is_test = FALSE")

    def test_currency_scale_detection(self):
        signals = self.extractor.extract_from_metadata(self.sample_metadata)
        currency_sigs = [s for s in signals if s.signal_type == "currency_scale"]
        self.assertEqual(len(currency_sigs), 2)
        tables = {s.table for s in currency_sigs}
        self.assertIn("invoices", tables)
        self.assertIn("refunds", tables)
        self.assertEqual(currency_sigs[0].metadata["scale"], 100)

    def test_implicit_foreign_key_detection(self):
        signals = self.extractor.extract_from_metadata(self.sample_metadata)
        fk_sigs = [s for s in signals if s.signal_type == "implicit_fk"]
        join_preds = {s.suggested_predicate for s in fk_sigs}
        self.assertIn("invoices.account_id = accounts.id", join_preds)
        self.assertIn("refunds.invoice_id = invoices.id", join_preds)

    def test_status_column_detection(self):
        signals = self.extractor.extract_from_metadata(self.sample_metadata)
        status_sigs = [s for s in signals if s.signal_type == "status_enum"]
        cols = {(s.table, s.column) for s in status_sigs}
        self.assertIn(("accounts", "plan_tier"), cols)
        self.assertIn(("invoices", "status"), cols)


class TestQueryLogMiner(unittest.TestCase):
    def setUp(self):
        self.miner = QueryLogMiner(min_support=0.5)
        self.queries = [
            "SELECT count(*) FROM accounts a WHERE a.is_test = false AND a.deleted_at IS NULL",
            "SELECT count(*) FROM accounts a JOIN subscriptions s ON a.id = s.account_id WHERE a.is_test = false AND a.deleted_at IS NULL AND s.status = 'active'",
            "SELECT count(*) FROM accounts a JOIN subscriptions s ON a.id = s.account_id WHERE a.is_test = false AND a.deleted_at IS NULL AND s.status = 'canceled'",
            "SELECT sum(i.amount_cents / 100) FROM invoices i JOIN accounts a ON a.id = i.account_id WHERE a.is_test = false AND a.deleted_at IS NULL AND i.status = 'paid'",
            "SELECT sum(i.amount_cents::numeric / 100) FROM invoices i WHERE i.status = 'paid' AND i.paid_at >= '2026-07-01' AND i.paid_at < '2026-10-01'",
        ]

    def test_predicate_mining_and_support(self):
        results = self.miner.mine_queries(self.queries)
        self.assertEqual(results.total_queries, 5)
        self.assertEqual(results.table_query_counts["accounts"], 4)

        # Invariants should include accounts.is_test = FALSE and accounts.deleted_at IS NULL (4/4 = 1.0 support)
        inv_sqls = {inv.predicate_sql for inv in results.invariants}
        self.assertIn("accounts.is_test = FALSE", inv_sqls)
        self.assertIn("accounts.deleted_at IS NULL", inv_sqls)

        # Invariant support should be 1.0 for accounts
        for inv in results.invariants:
            if inv.table == "accounts":
                self.assertEqual(inv.support, 1.0)
                self.assertEqual(inv.occurrences, 4)

    def test_dynamic_filter_exclusion(self):
        results = self.miner.mine_queries(self.queries)
        inv_sqls = {inv.predicate_sql for inv in results.invariants}
        # Temporal interval filters should NOT be promoted to invariant rules
        for sql in inv_sqls:
            self.assertNotIn("2026-07-01", sql)
            self.assertNotIn("2026-10-01", sql)

    def test_join_mining(self):
        results = self.miner.mine_queries(self.queries)
        join_sqls = {j.join_sql for j in results.joins}
        self.assertIn("accounts.id = subscriptions.account_id", join_sqls)
        self.assertIn("accounts.id = invoices.account_id", join_sqls)

    def test_currency_metric_mining(self):
        results = self.miner.mine_queries(self.queries)
        self.assertTrue(any(m.table == "invoices" and m.column == "amount_cents" for m in results.metrics))

    def test_mine_yaml_file(self):
        data = [
            {"id": "q1", "gold_sql": "SELECT * FROM accounts WHERE is_test = false AND deleted_at IS NULL"},
            {"id": "q2", "gold_sql": "SELECT * FROM accounts WHERE is_test = false AND deleted_at IS NULL"},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            tmp_path = f.name

        try:
            results = self.miner.mine_file(tmp_path)
            self.assertEqual(results.total_queries, 2)
            self.assertEqual(results.invariants[0].table, "accounts")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestRuleSynthesizer(unittest.TestCase):
    def test_synthesis_and_corroboration(self):
        extractor = SchemaSignalExtractor()
        metadata = {
            "accounts": [
                {"name": "id", "type": "INTEGER"},
                {"name": "is_test", "type": "BOOLEAN"},
                {"name": "deleted_at", "type": "TIMESTAMP"},
            ],
            "invoices": [
                {"name": "id", "type": "INTEGER"},
                {"name": "amount_cents", "type": "INTEGER"},
            ],
        }
        signals = extractor.extract_from_metadata(metadata)

        miner = QueryLogMiner()
        queries = [
            "SELECT * FROM accounts WHERE is_test = false AND deleted_at IS NULL",
            "SELECT sum(amount_cents / 100) FROM invoices",
        ]
        mining_results = miner.mine_queries(queries, schema_metadata=metadata)

        synth = RuleSynthesizer(schema_signals=signals, mining_results=mining_results)
        rules = synth.synthesize()

        # Verify entity filter rule
        entity_rules = [r for r in rules if r.category == "entity_filter"]
        self.assertEqual(len(entity_rules), 1)
        self.assertEqual(entity_rules[0].target_table, "accounts")
        self.assertEqual(entity_rules[0].confidence, 1.0)
        self.assertIn("corroborated", entity_rules[0].support_source)

        # Verify currency scale rule
        currency_rules = [r for r in rules if r.category == "currency_scale"]
        self.assertEqual(len(currency_rules), 1)
        self.assertEqual(currency_rules[0].target_table, "invoices")
        self.assertIn("amount_cents", currency_rules[0].sql_predicate_or_expr)

        # Verify markdown output
        md = synth.to_markdown(db_name="testdb")
        self.assertIn("## testdb (Discovered Business Rules & Schema Invariants)", md)
        self.assertIn("accounts.deleted_at IS NULL", md)
        self.assertIn("amount_cents::numeric / 100", md)

        # Verify JSON export
        json_str = synth.to_json()
        parsed = json.loads(json_str)
        self.assertIn("rules", parsed)
        self.assertGreater(len(parsed["rules"]), 0)


class TestRunnerIntegration(unittest.TestCase):
    def test_get_induced_rules_text(self):
        # Verify get_induced_rules_text runs cleanly for appdb
        rules_text = get_induced_rules_text("appdb", force_refresh=True)
        self.assertIn("## appdb", rules_text)
        self.assertIn("accounts.deleted_at IS NULL", rules_text)
        self.assertIn("accounts.is_test = FALSE", rules_text)


if __name__ == "__main__":
    unittest.main()

