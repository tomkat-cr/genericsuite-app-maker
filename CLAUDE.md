# CLAUDE.md

This file provides guidance to AI Coding Assistants (Claude Code, Gemini CLI, Cursor, Antigravity, etc.) when working with code in this repository.

## Project Overview

**GSAM (GenericSuite App Maker)** is an AI-powered development assistant that helps with software application ideation, design, and code generation. It offers:

- **Streamlit web UI** (`streamlit_app.py`) for interactive development sessions
- **FastAPI agent** (`gsam_ottomator_agent_app.py`) for integration with OTTomator Live Agent Studio
- Multi-provider LLM support (OpenAI, Together.ai, Groq, HuggingFace, OpenRouter, Ollama, xAI, Nvidia NIMs, AI/ML API)
- Full lifecycle: ideation → naming → structure → DB schema → slides → code generation
- Media generation: text-to-image (Flux, DALL-E) and text-to-video (Rhymes Allegro)
- Embedding-based code generation via LlamaIndex (RAG instead of full attachment context)

## Commands

```bash
# Environment setup
make create_venv      # Create Python virtual environment
make install          # Install dependencies

# Running
make run              # Run Streamlit app (localhost:8501)
# or
bash scripts/run_app.sh run

# Testing & QA
make test             # Run pytest
make lint             # Run prospector linter
make types            # Run mypy type checking
make coverage         # Run coverage analysis
make format           # Format with yapf
make format_check     # Check formatting without modifying
make pycodestyle      # Check code style compliance
make qa               # Run all QA checks

# Security
make sast-test        # Security scan with Snyk

# Agent (Docker-based FastAPI)
cd gsam_ottomator_agent
make install          # Build Docker image
make run              # Run agent (localhost:8001)
make logs             # View container logs
make stop             # Stop container
```

## Architecture

### Layer Structure

**Presentation Layer**
- `streamlit_app.py` — Main Streamlit UI entry point
- `gsam_ottomator_agent_app.py` — FastAPI entry point exposing `/api/gsam-supabase-agent` and `/api/gsam-postgres-agent`
- `src/` — UI components (`codegen_app_ideation.py`, `codegen_buttons.py`)

**Business Logic Layer** (`lib/`)
- `codegen_streamlit_lib.py` — Streamlit session/state management
- `codegen_pydantic_ai.py` — Pydantic AI wrapper for LLM orchestration
- `codegen_ai_abstracts.py` — Base LLM provider interface (all providers extend this)
- `codegen_ai_utilities.py` — Provider factory; selects and instantiates the right provider class
- `codegen_ai_provider_*.py` (11 files) — One file per provider: `openai`, `openrouter`, `together_ai`, `groq`, `huggingface`, `ollama`, `nvidia`, `xai`, `rhymes` (video), `aimlapi`
- `codegen_schema_generator.py` — DB schema + code generation using LlamaIndex embeddings
- `codegen_ideation_lib.py` / `codegen_app_ideation_lib.py` — App ideation logic
- `codegen_generation_lib.py` — Text/image/video generation routing
- `codegen_powerpoint.py` — PowerPoint slide generation
- `codegen_db.py` / `codegen_db_abstracts.py` / `codegen_db_json.py` / `codegen_db_mongodb.py` — DB abstraction layer

**Agent Layer** (`gsam_ottomator_agent/`)
- `gsam_agent_lib.py` — Shared agent logic with Pydantic AI
- `gsam_supabase_agent.py` / `gsam_postgres_agent.py` — DB-specific agent variants
- Deployed in Docker; see `Dockerfile` and `base_python_docker/`

**Data Persistence**
- MongoDB Atlas (default for Streamlit UI)
- JSON files in `/db/` (local fallback)
- PostgreSQL / Supabase (agent mode)

### Key Data Flows

**Text/Image/Video generation:**
```
User Input → StreamlitLib → codegen_ai_utilities (provider factory)
→ Provider class (codegen_ai_provider_*.py) → LLM API → Save to DB → Display
```

**Schema/code generation with RAG:**
```
User Input → codegen_schema_generator → LlamaIndex vector index
→ Query embeddings → Custom LLM interface → Provider → JSON config + Python code
```

**Agent request:**
```
HTTP POST → Token verification → Parse AgentRequest
→ gsam_agent_lib (Pydantic AI) → LLM calls → DB storage → AgentResponse
```

### Configuration

All runtime behavior is driven by configuration, not code changes:

- `config/app_config.json` — Provider list, model options, feature toggles, DB paths, gallery settings, system prompt references
- `config/*.txt` — 13 system prompt files (one per generation task)
- `.env` — API keys for all providers, DB credentials, Ollama endpoint
- `schema_generator_ref_files.json` — Reference documents for embedding-based generation

### Adding a New LLM Provider

1. Create `lib/codegen_ai_provider_<name>.py` extending `codegen_ai_abstracts.py`
2. Register the provider in `codegen_ai_utilities.py` (provider factory)
3. Add provider config and models to `config/app_config.json`
4. Add required API key to `.env.example`

### Important Runtime Notes

- Python 3.10+ required; pure Python project (no Node.js)
- `nest_asyncio` is used to handle event loop conflicts between Streamlit and async providers
- The `SIMPLE_PAI_AGENT` constant (in agent lib) controls whether only OpenAI/OpenRouter are available (`True`) or all configured providers (`False`, default)
- Ollama runs locally; endpoint configured via `OLLAMA_API_URL` in `.env`
- Generated images saved to `/images/`, other outputs to `/output/`
- Embedding source documents placed in `/embeddings_sources/`

## Important Notes

- The files `AGENTS.md`, `GEMINI.md`, etc. (if present) have only a referece to `@CLAUDE.md` — edit only `CLAUDE.md`.
- Skills, commands, rules, and sub-agents are located in the `.claude/` directory.
