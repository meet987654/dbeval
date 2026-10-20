# Datus Evaluation Notes

## Tool Overview
- **Name:** Datus (`datus-agent`)
- **Repo/Docs:** https://github.com/datus-ai / https://datus.ai
- **Standard:** Apache Ossie (Open Semantic / Ontology Standard)

## Checklist (Day 0 Step 4)
- [x] **Postgres Support:** Yes. Has first-class PostgreSQL connector (`datus-postgresql`) and storage/vector engine (`datus-storage-postgresql`).
- [x] **Headless / Automated Execution:** Yes. Exposes multiple programmatic surfaces: headless Datus-CLI, Python SDK / REST APIs, and native Model Context Protocol (MCP) server.
- [x] **Supported LLM Providers:** Supports OpenAI, Anthropic, and standard OpenAI-compatible API providers.
  - **Mistral / codestral-2508 compatibility:** Fully compatible. Connects directly using standard OpenAI format with `base_url="https://api.mistral.ai/v1"`, `api_key=MISTRAL_API_KEY`, and model `codestral-2508`.

## Setup & Execution Notes
- Automated semantic modeling parses schema & historical query logs into OSI semantic models.
- Can be run programmatically via Python SDK or queried over MCP.

## Setup Log
- **Start Time:** 
- **End Time:** 
- **Time Taken:** 

### Steps Taken
1. 

### Problems & Gotchas
- 

### First Impressions
- 
