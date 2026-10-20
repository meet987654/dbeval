# Wren Evaluation Notes

## Tool Overview
- **Name:** Wren AI / Wren Engine
- **Repo/Docs:** https://github.com/Canner/WrenAI
- **Official site:** https://getwren.ai
- **Standard:** MDL (Modeling Definition Language)

## Checklist (Day 0 Step 4)
- [x] **Postgres Support:** Yes. Introspects PostgreSQL databases natively and generates MDL models for metrics and relationships.
- [x] **Headless / Automated Execution:** Yes. Features native Model Context Protocol (MCP) server daemon (`wren serve mcp` over `stdio` or HTTP), as well as REST APIs and Python SDK bindings.
- [x] **Supported LLM Providers:** Supports OpenAI, Anthropic, Azure OpenAI, Google Gemini, Ollama, and custom OpenAI-compatible endpoints.
  - **Mistral / codestral-2508 compatibility:** Fully compatible. Connects directly using standard OpenAI format with `OPENAI_API_BASE=https://api.mistral.ai/v1`, `OPENAI_API_KEY=MISTRAL_API_KEY`, and model `codestral-2508`.

## Setup & Execution Notes
- Native MCP daemon (`wren serve mcp`) enables AI agents to query semantic models directly.
- Uses read-only mode for querying and model compilation.

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
