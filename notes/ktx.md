# ktx Evaluation Notes

## Tool Overview
- **Name:** ktx
- **Repo/Docs:** https://github.com/kaelio/ktx
- **Official site:** https://kaelio.com
- **Package:** `@kaelio/ktx` (npm)
- **Version:** `@kaelio/ktx@0.16.0`

## Checklist (Day 0 Step 4)
- [x] **Postgres Support:** Yes. Supports PostgreSQL (`postgres`), MySQL, ClickHouse, BigQuery, Snowflake, DuckDB, SQLite, SQL Server, Athena.
- [x] **Headless / Automated Execution:** Yes. Provides a headless CLI command and native Model Context Protocol (MCP) server daemon (`ktx mcp start` / `stdio`), allowing programmatic invocation by AI agents.
- [x] **Supported LLM Providers:** Supports Anthropic (Claude), Google Vertex AI, local agent runtimes (`claude-code`, `codex`), and Vercel AI `gateway`.
  - **Mistral / codestral-2508 compatibility:** Fully verified. `ktx` accepts Mistral's OpenAI-compatible base URL (`https://api.mistral.ai/v1`) using `backend: gateway` with `gateway.api_key: env:MISTRAL_API_KEY` and model `codestral-2508`. Tested with `ktx status` -> `LLM gateway · codestral-2508 ✓ key set`.

## Setup & Execution Notes
- Global install: `npm install -g @kaelio/ktx`
- Setup command: `ktx setup`
- Headless / MCP runner: `ktx mcp start`

## Setup Log
- **Date:** Day 0
- **Time Taken:** ~15 minutes

### Steps Taken
1. Installed CLI globally: `npm install -g @kaelio/ktx` (version 0.16.0).
2. Initialized project directory: `ktx admin init ktx_olist`. Scaffolded `.ktx/`, `raw-sources/`, `semantic-layer/`, `wiki/`, and `ktx.yaml`.
3. Configured PostgreSQL connection in `ktx_olist/ktx.yaml`:
   ```yaml
   connections:
     olist:
       driver: postgres
       url: postgresql://reader:reader@localhost:5433/olist
   ```
4. Tested connection: `ktx --project-dir ktx_olist connection test` -> passed (`olist postgres ✓ ok`).
5. ktx automatically installed and configured its managed Python runtime (`~/.ktx/runtime/0.16.0` using `uv 0.11.21`).
6. Tested read-only SQL: `ktx --project-dir ktx_olist sql -c olist "SELECT count(*) FROM orders"` -> returned `99441`.
7. Attempted `ktx ingest olist --yes` -> confirmed that schema enrichment/scanning requires configuring an LLM provider and embeddings.

### Problems & Gotchas
- **Repository Conflict:** `ktx setup` requires its own folder/git repo. Running it inside an existing git workspace throws: `dbeval is already a git repository that ktx did not create. ktx keeps its context in a repository it owns.` Solution: keep tool context in a dedicated subfolder (`ktx_olist`) with `--project-dir`.
- **Config Key Format:** The discriminator key in `ktx.yaml` is `driver: postgres` (not `type`).
- **Enrichment Prerequisite:** Full ingestion (`ktx ingest`) requires LLM model and embedding keys configured to generate relationship and metric definitions.

### First Impressions
- Very smooth CLI and fast runtime provisioning via `uv`.
- Excellent strictness: built-in parser-validated read-only SQL enforcement.
- Clean separation of concerns with `.ktx/` state, `wiki/`, and `semantic-layer/` directories.
