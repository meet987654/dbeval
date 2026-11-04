#!/usr/bin/env python3
"""Unit tests for runners/baseline.py, local runner support, and SQLite zero-Docker mode."""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "db"))

from baseline import (
    adapt_sql_for_sqlite,
    call_llm,
    dispose_engine,
    extract_sql,
    looks_read_only,
    run_sql,
    schema_text,
    _schema_cache,
)
import seed_appdb as s


def test_extract_sql():
    assert extract_sql("SELECT 1;") == "SELECT 1"
    assert extract_sql("  SELECT COUNT(*) FROM table;  ") == "SELECT COUNT(*) FROM table"
    fenced = "```sql\nSELECT id, name FROM accounts WHERE deleted_at IS NULL;\n```"
    assert extract_sql(fenced) == "SELECT id, name FROM accounts WHERE deleted_at IS NULL"
    fenced_no_tag = "```\nSELECT 42\n```"
    assert extract_sql(fenced_no_tag) == "SELECT 42"


def test_looks_read_only():
    assert looks_read_only("SELECT * FROM accounts") is True
    assert looks_read_only("WITH cte AS (SELECT 1) SELECT * FROM cte") is True
    assert looks_read_only("  select count(*) from users") is True
    assert looks_read_only("DROP TABLE accounts") is False
    assert looks_read_only("INSERT INTO accounts VALUES (1)") is False
    assert looks_read_only("UPDATE accounts SET is_test = true") is False
    assert looks_read_only("SELECT 1; DROP TABLE users") is False


def test_adapt_sql_for_sqlite():
    sql1 = "SELECT SUM(i.amount_cents::numeric / 100 * f.usd_per_unit) FROM invoices i"
    adapted1 = adapt_sql_for_sqlite(sql1)
    assert "::numeric" not in adapted1
    assert "CAST(i.amount_cents AS NUMERIC)" in adapted1

    sql2 = "SELECT id::text FROM accounts"
    adapted2 = adapt_sql_for_sqlite(sql2)
    assert "::text" not in adapted2
    assert adapted2 == "SELECT id FROM accounts"


def test_call_llm_ollama_configuration():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="SELECT 1"))]
    mock_response.usage.prompt_tokens = 15
    mock_response.usage.completion_tokens = 5

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    env = {
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "qwen2.5-coder:14b",
        "OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            content, t_in, t_out = call_llm("system prompt", "user prompt")

            assert content == "SELECT 1"
            assert t_in == 15 and t_out == 5
            mock_openai_cls.assert_called_once()
            _, kwargs = mock_openai_cls.call_args
            assert kwargs.get("base_url") == "http://127.0.0.1:11434/v1"
            assert kwargs.get("api_key") == "ollama"


def test_call_llm_vllm_configuration():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="SELECT 42"))]
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.completion_tokens = 8

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    env = {
        "LLM_PROVIDER": "vllm",
        "LLM_MODEL": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "VLLM_BASE_URL": "http://127.0.0.1:8000/v1",
    }
    with patch.dict(os.environ, env, clear=False):
        with patch("openai.OpenAI", return_value=mock_client) as mock_openai_cls:
            content, t_in, t_out = call_llm("system prompt", "user prompt")

            assert content == "SELECT 42"
            mock_openai_cls.assert_called_once()
            _, kwargs = mock_openai_cls.call_args
            assert kwargs.get("base_url") == "http://127.0.0.1:8000/v1"
            assert kwargs.get("api_key") == "dummy"


def test_call_llm_unknown_provider():
    env = {
        "LLM_PROVIDER": "unknown_provider_xyz",
        "LLM_MODEL": "test-model",
    }
    with patch.dict(os.environ, env, clear=False):
        try:
            call_llm("system", "user")
            assert False, "Expected ValueError for unknown provider"
        except ValueError as e:
            assert "Unknown LLM_PROVIDER" in str(e)


def test_sqlite_seeding_and_execution():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        sqlite_file = os.path.join(tmpdir, "test_appdb.sqlite")
        s.seed_database(sqlite_path=sqlite_file)

        assert os.path.exists(sqlite_file)

        env = {"READER_URL_APPDB": f"sqlite:///{os.path.abspath(sqlite_file)}"}
        with patch.dict(os.environ, env, clear=False):
            _schema_cache.clear()
            schema = schema_text("appdb")
            assert "TABLE accounts" in schema
            assert "TABLE invoices" in schema
            assert "CONSTRAINT FOREIGN KEY" in schema

            # Test basic queries via run_sql
            cols, rows = run_sql("appdb", "SELECT COUNT(*) FROM accounts WHERE is_test = false AND deleted_at IS NULL")
            assert cols == ["COUNT(*)"]
            assert rows[0][0] == 1745

            # Test query with ::numeric adaptation
            cols2, rows2 = run_sql(
                "appdb",
                "SELECT ROUND(SUM(i.amount_cents::numeric / 100 * f.usd_per_unit), 2) "
                "FROM invoices i JOIN fx_rates f ON f.currency = i.currency "
                "JOIN accounts a ON a.id = i.account_id "
                "WHERE i.status = 'paid' AND i.paid_at >= '2026-07-01 00:00:00+00' AND i.paid_at < '2026-10-01 00:00:00+00' "
                "AND a.is_test = false AND a.deleted_at IS NULL"
            )
            assert rows2[0][0] == 267373.95

            dispose_engine("appdb")


def run_all_tests():
    test_extract_sql()
    test_looks_read_only()
    test_adapt_sql_for_sqlite()
    test_call_llm_ollama_configuration()
    test_call_llm_vllm_configuration()
    test_call_llm_unknown_provider()
    test_sqlite_seeding_and_execution()
    print("baseline.py: all unit tests passed")


if __name__ == "__main__":
    run_all_tests()
