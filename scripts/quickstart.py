#!/usr/bin/env python3
"""Quickstart script for dbeval:
1. Verifies Docker and LLM API credentials.
2. Starts the Postgres test database (docker compose up -d).
3. Seeds appdb with deterministic data (db/seed_appdb.py).
4. Runs baseline and baseline_rules on 10 appdb questions for 1 run.
5. Scores both systems and prints the results.
"""

import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, os.path.join(ROOT, "scorer"))

# Load .env if present
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass


def check_docker():
    """Verify docker command exists and daemon is running."""
    if not shutil.which("docker"):
        print("[Error] Docker CLI is not found on your PATH.")
        print("Please install Docker Desktop (or your Docker engine) and try again.")
        sys.exit(1)

    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        if res.returncode != 0:
            raise RuntimeError("docker info returned non-zero")
    except Exception:
        print("[Error] Docker daemon is not running or unreachable.")
        print("Please start Docker Desktop (or the Docker daemon) and try again.")
        sys.exit(1)


def check_api_key():
    """Verify at least one supported LLM API key is set."""
    provider = os.getenv("LLM_PROVIDER", "").lower()

    if not provider:
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("MISTRAL_API_KEY"):
            provider = "mistral"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("GROQ_API_KEY"):
            provider = "groq"
        else:
            print("[Error] Missing LLM API key.")
            print("Please configure your LLM provider and API key in .env or your environment:")
            print("  LLM_PROVIDER=mistral   # or anthropic, openai, groq")
            print("  LLM_MODEL=codestral-2508")
            print("  MISTRAL_API_KEY=your_api_key_here")
            print("\nSee .env.example for template.")
            sys.exit(1)
        os.environ["LLM_PROVIDER"] = provider

    key_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "groq": "GROQ_API_KEY",
    }
    key_var = key_map.get(provider, "OPENAI_API_KEY")
    if not os.getenv(key_var) and not os.getenv("OPENAI_API_KEY"):
        print(f"[Error] Missing {key_var} for LLM_PROVIDER={provider}.")
        print(f"Please export {key_var} or add it to your .env file.")
        sys.exit(1)

    if not os.getenv("LLM_MODEL"):
        default_models = {
            "anthropic": "claude-3-5-sonnet-20241022",
            "mistral": "codestral-2508",
            "openai": "gpt-4o",
            "groq": "llama-3.3-70b-versatile",
        }
        os.environ["LLM_MODEL"] = default_models.get(provider, "codestral-2508")


def check_python_dependencies():
    """Verify core python runner dependencies."""
    missing = []
    for pkg in ["yaml", "sqlalchemy"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[Error] Missing required python package(s): {', '.join(missing)}")
        print("Please install requirements first: pip install -r requirements.txt")
        sys.exit(1)


def wait_for_postgres(timeout_seconds=30):
    """Wait until PostgreSQL on port 5433 accepts connections."""
    import baseline as b

    engine = b.make_engine("postgresql://postgres:postgres@localhost:5433/postgres")
    started = time.time()
    while time.time() - started < timeout_seconds:
        try:
            from sqlalchemy import text

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    print("=" * 65)
    print(" dbeval Quickstart: Baseline vs. Baseline + Rules")
    print("=" * 65)

    print("\n[1/5] Checking environment & credentials...")
    check_docker()
    check_api_key()
    check_python_dependencies()
    print("  -> Docker daemon is running.")
    print(f"  -> LLM provider: {os.getenv('LLM_PROVIDER')} (model: {os.getenv('LLM_MODEL')})")

    print("\n[2/5] Starting database container (docker compose up -d)...")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=ROOT, check=True)
    print("  -> Waiting for PostgreSQL on localhost:5433...")
    if not wait_for_postgres():
        print("[Error] PostgreSQL did not become ready in time.")
        sys.exit(1)
    print("  -> PostgreSQL is ready.")

    print("\n[3/5] Seeding synthetic appdb SaaS database...")
    subprocess.run([sys.executable, os.path.join(ROOT, "db", "seed_appdb.py")], cwd=ROOT, check=True)
    print("  -> appdb seeded successfully.")

    print("\n[4/5] Running 10 appdb questions across baseline and baseline_rules...")
    import yaml
    import baseline as b
    import controls as c
    from compare import same

    questions_file = os.path.join(ROOT, "questions", "appdb.yaml")
    with open(questions_file, "r", encoding="utf-8") as f:
        all_questions = yaml.safe_load(f)

    subset = all_questions[:10]
    baseline_passed = 0
    rules_passed = 0

    for idx, q in enumerate(subset, 1):
        qid = q["id"]
        qtext = q["question"]
        gold_sql = q["gold_sql"]
        ordered = q.get("ordered", False)

        print(f"  [{idx}/10] {qid}: {qtext[:50]}...")

        # Run gold SQL
        try:
            _, gold_rows = b.run_sql("appdb", gold_sql)
        except Exception as e:
            print(f"    Gold SQL failed: {e}")
            continue

        # Run baseline (schema only + samples)
        r_base = b.answer("appdb", qtext)
        base_ok = False
        if not r_base.get("error"):
            base_ok = same(gold_rows, r_base.get("rows", []), ordered=ordered)
        if base_ok:
            baseline_passed += 1

        # Run baseline_rules (schema + prompt rules)
        r_rules = c.answer_baseline_rules("appdb", qtext)
        rules_ok = False
        if not r_rules.get("error"):
            rules_ok = same(gold_rows, r_rules.get("rows", []), ordered=ordered)
        if rules_ok:
            rules_passed += 1

        print(f"       baseline: {'PASS' if base_ok else 'FAIL'} | baseline_rules: {'PASS' if rules_ok else 'FAIL'}")

    print("\n[5/5] Quickstart Results")
    print("=" * 65)
    print(f"  baseline (raw schema + samples):   {baseline_passed} / 10 ({baseline_passed * 10.0:.1f}%)")
    print(f"  baseline_rules (prompt rules):     {rules_passed} / 10 ({rules_passed * 10.0:.1f}%)")
    print("=" * 65)
    print("Expected Outcome:")
    print("  - baseline is low: fails on SaaS traps (is_test accounts, soft deletes,")
    print("    cents conversion, refund netting) because table schemas alone omit business rules.")
    print("  - baseline_rules is high: prompt rules explicitly clarify business logic,")
    print("    lifting accuracy significantly on the identical model and schema.")
    print("\nTo run the full suite across all systems and databases, see README.md.")


if __name__ == "__main__":
    main()
