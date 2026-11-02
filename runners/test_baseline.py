#!/usr/bin/env python3
"""Unit tests for runners/baseline.py and local runner support."""

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline import extract_sql, looks_read_only, call_llm


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


def run_all_tests():
    test_extract_sql()
    test_looks_read_only()
    test_call_llm_ollama_configuration()
    test_call_llm_vllm_configuration()
    test_call_llm_unknown_provider()
    print("baseline.py: all unit tests passed")


if __name__ == "__main__":
    run_all_tests()
