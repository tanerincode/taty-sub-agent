# 📦 Setup & Configuration

## Requirements

- Python 3.11+
- An Anthropic API key (Claude) and/or OpenAI API key

---

## Installation

```bash
git clone https://github.com/tombastaner/taty-sub-agent
cd taty-sub-agent

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_MODEL=claude-sonnet-4-6

# OpenAI (optional)
OPENAI_API_KEY=sk-proj-...
OPENAI_DEFAULT_MODEL=gpt-4o

# Agent settings
MAX_PARALLEL_AGENTS=5
MAX_TOKENS=8096

# Workspace for file tools (defaults to project root)
AGENT_WORKSPACE=/path/to/your/workspace
```

---

## Augment (VS Code)

Add to your `settings.json`:

```json
"augment.advanced": {
  "mcpServers": [
    {
      "name": "taty-sub-agent",
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["src/server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/taty-sub-agent",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DEFAULT_MODEL": "claude-sonnet-4-6",
        "OPENAI_API_KEY": "sk-proj-...",
        "OPENAI_DEFAULT_MODEL": "gpt-4o",
        "MAX_PARALLEL_AGENTS": "5"
      }
    }
  ]
}
```

Restart the MCP server from **Augment Settings → MCP → taty-sub-agent → Restart**.

---

## Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "taty-sub-agent": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["src/server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/taty-sub-agent",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DEFAULT_MODEL": "claude-sonnet-4-6"
      }
    }
  }
}
```

Restart Claude Desktop to pick up the changes.

---

## Running the MCP server manually

```bash
PYTHONPATH=. python src/server.py
```

---

## Running a task directly (no MCP)

```bash
python main.py
```

---

## Seeding skills into Synatyx memory

```bash
python scripts/seed_skills.py
```

This reads all `.md` files from `skills/` and uploads them to Synatyx for RAG matching.

