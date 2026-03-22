<div align="center">

# 🤖 taty-sub-agent

**RAG-powered multi-agent dispatch over MCP.**
Delegate tasks to specialized sub-agents that think, write files, run commands, and ship — all from inside your editor.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?style=flat-square)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.1-purple?style=flat-square)](https://gofastmcp.com)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-orange?style=flat-square)](https://anthropic.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green?style=flat-square)](https://openai.com)

**by [Taner Tombas](https://github.com/tanerincode)**

</div>

---

## What is this?

`taty-sub-agent` is an MCP server that exposes **specialized AI sub-agents** as tools. Each sub-agent is powered by a skill — a role definition that shapes how it thinks and writes code. When you give it a task, it:

1. **Routes** — RAG-matches the best skill for the task (or you pick one by name)
2. **Thinks** — runs a full tool-calling loop against Claude or GPT-4o
3. **Acts** — writes files, reads context, runs commands, and iterates until done
4. **Returns** — the final output and everything it created on disk

No round-trips. No copy-pasting. The sub-agent just ships.

---

## Architecture

```
You / Augment
     │
     ▼  MCP (stdio)
 taty-sub-agent server
     │
     ├── RAG skill router  ──▶  Synatyx memory
     │
     ├── AgentInvoker
     │       │
     │       ▼  tool-calling loop
     │   Anthropic / OpenAI
     │       │
     │       ▼
     │   [ write_file | read_file | list_directory | run_command ]
     │
     └── result + files on disk
```

---

## Quick Start

```bash
git clone https://github.com/tanerincode/taty-sub-agent
cd taty-sub-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> Full setup including `.env` and MCP client config → **[docs/setup.md](docs/setup.md)**

---

## MCP Tools

| Tool | What it does |
|---|---|
| `invoke_agent` | Run a single skill-matched sub-agent for a task |
| `invoke_parallel` | Run multiple sub-agents concurrently |
| `list_skills` | List all available skills |

> Detailed examples and parameters → **[docs/usage.md](docs/usage.md)**

---

## Built-in Skills

| Skill | Role |
|---|---|
| `python-developer` | FastAPI, asyncio, Pydantic, pytest |
| `nodejs-developer` | Node.js APIs, services, tooling |
| `code-reviewer` | Security, quality, and best-practice reviews |

> How skills work and how to write your own → **[docs/skills.md](docs/skills.md)**

---

## Sub-agent Tools

Each sub-agent runs a live tool-calling loop and can:

- 📝 `write_file` — create or overwrite files on disk
- 📖 `read_file` — read existing files for context
- 📂 `list_directory` — explore the workspace
- ⚡ `run_command` — execute shell commands (30s timeout)

> Full reference → **[docs/tools.md](docs/tools.md)**

---

## Synatyx Dependency

`taty-sub-agent` uses **[Synatyx](https://github.com/tanerincode/taty-v2)** as its long-term memory and RAG backend — a persistent context engine built for AI assistants that gives them memory across sessions via MCP.

Synatyx provides:

- **Skill storage & semantic retrieval** — skills are embedded into Qdrant and matched to tasks via vector search
- **Result persistence** — agent outputs are stored in L2 (episodic) memory for future context
- **4-layer memory model** — L1 (transient/Redis), L2 (episodic), L3 (semantic/Qdrant), L4 (user-global/PostgreSQL)
- **Per-project namespacing** — each project gets its own Qdrant collection (`ctx_<slug>`)

### Remote (recommended)

Synatyx can be self-hosted or run remotely as an HTTP/SSE MCP server (`RUN_MODE=mcp-http`). Once deployed, point your MCP client at:

```
http://<your-host>:9001/mcp/sse
```

### Running locally

Clone [Synatyx](https://github.com/tanerincode/synatyx) and start the infrastructure with Docker Compose:

```bash
git clone https://github.com/tanerincode/synatyx
cd synatyx
docker compose up -d
```

This starts Qdrant, Redis, PostgreSQL, runs Alembic migrations, and launches the garbage collection daemon. The MCP server itself runs outside Docker — add it to your `.mcp.json`:

```json
"synatyx": {
  "command": "/path/to/synatyx/.venv/bin/python3",
  "args": ["/path/to/synatyx/main.py"],
  "env": {
    "RUN_MODE": "mcp",
    "QDRANT_HOST": "localhost",
    "QDRANT_PORT": "6333",
    "REDIS_URL": "redis://localhost:6379/0",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "context_engine",
    "POSTGRES_USER": "context_engine",
    "POSTGRES_PASSWORD": "context_engine"
  }
}
```

### Without Synatyx

`taty-sub-agent` degrades gracefully — if Synatyx is unavailable, skill routing falls back to local keyword matching against `skills/*.md` files. All core functionality still works.

---

## Project Structure

```
skills/           Skill definitions (.md)
src/
  agent/
    invoker.py    Orchestrates routing + model calls
    tools.py      Sub-agent tools (file I/O, shell)
  core/
    config.py     Settings via pydantic-settings + .env
    models.py     AgentTask, AgentResult, Skill, ...
  memory/
    synatyx.py    RAG skill lookup + result storage
  providers/
    anthropic.py  Claude tool-calling loop
    openai.py     GPT-4o tool-calling loop
  skills/
    loader.py     Parses skill .md files from disk
    router.py     RAG routing + local fallback
  server.py       FastMCP MCP server entry point
scripts/
  seed_skills.py  Seed local skills into Synatyx
docs/             Extended documentation
tests/            pytest test suite
```

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

