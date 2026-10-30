# Contributing to dbeval

Thank you for your interest in contributing to **dbeval**! This repository is dedicated to reproducible, head-to-head benchmarking of Text-to-SQL context layers and semantic systems over PostgreSQL.

We welcome contributions ranging from bug fixes in adapters to new database schemas, question suites, and evaluation runners.

---

## Code of Conduct

Please treat all contributors and maintainers with kindness, professional courtesy, and constructive feedback.

---

## Development Setup

### Prerequisites

- **Python**: 3.11 or 3.12
- **Docker & Docker Compose**: For spinning up local PostgreSQL instances
- **Git**

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/meet987654/dbeval.git
   cd dbeval
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your LLM provider credentials (Mistral, Anthropic, OpenAI, etc.)
   ```

---

## Quick Verification

Before making changes, verify that the test harness and analysis scripts run cleanly:

1. **Verify Python compilation & basic tests:**
   ```bash
   python -m compileall runners scorer db scripts
   ```

2. **Run headline zero-setup analysis:**
   ```bash
   python scorer/analyze.py results/raw/suite_results_all.csv --ties half --matrix /tmp/per_question.csv
   ```

3. **Run local quickstart (requires Docker + 1 LLM API key):**
   ```bash
   python scripts/quickstart.py
   ```

---

## How to Contribute

### 1. Proposing Fixes to Existing Runners or Scorer

- Ensure changes do not break reproducibility or modify frozen benchmark runs (`results/raw/suite_results_all.csv`).
- Maintain formatting and lint standards using `ruff`.

### 2. Adding a New Context Layer / System Under Test

When integrating a new semantic layer or data-agent context system:
1. Add a dedicated runner in `runners/` implementing the `answer(db_name: str, question: str) -> dict` interface.
2. The runner should return a dict with `{"sql": str, "rows": list, "latency": float, "error": Optional[str]}`.
3. Keep semantic layer definitions self-contained under their respective directories (e.g. `layers/<system_name>/`).
4. Avoid hardcoding test question solutions in prompt templates or layer definitions.

### 3. Adding New Questions or Benchmarks

- Store question specifications in YAML under `questions/<db_name>.yaml`.
- Include `id`, `question`, `gold_sql`, and `ordered` (boolean indicating if row ordering matters).
- Run `python scorer/validate_gold.py` to ensure the gold SQL executes cleanly against the live seeded database.

---

## Pull Request Guidelines

1. **Create a feature branch:**
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Commit with clear messages:** Use conventional commit formatting (e.g., `feat:`, `fix:`, `docs:`, `test:`).
3. **Ensure CI passes:** Every commit should compile cleanly and pass syntax checks.
4. **Submit your PR:** Describe the rationale, what changed, and how it was tested.

---

## Upstream Issues & Contributions

If your contribution identifies an issue in an upstream tool (such as ktx, Wren Engine, or Datus):
- Open an issue upstream with minimal reproduction steps.
- Reference the upstream issue in your PR description.
- Follow honest upstream wording ("issue filed", "fix proposed in PR", open until merged).
