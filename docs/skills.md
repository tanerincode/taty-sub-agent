# 🧠 Skills

Skills are the role definitions that give each sub-agent its personality, standards, and output format. They live in `skills/*.md`.

---

## Skill File Format

```markdown
---
name: python-developer
description: Senior Python developer for backend services, APIs, and tooling
---
You are a senior Python developer with deep expertise in FastAPI, SQLAlchemy,
Pydantic, asyncio, and modern Python patterns.

## Responsibilities
- Write clean, production-ready Python code (3.11+)
- Design and implement FastAPI services, background workers, and CLI tools
...
```

### Frontmatter fields

| Field | Required | Description |
|---|---|---|
| `name` | yes | Unique skill identifier (used for explicit routing) |
| `description` | yes | One-line summary — used for RAG matching |

Everything below the closing `---` is the system prompt sent to the model.

---

## Built-in Skills

### `python-developer`
Senior Python developer. Specializes in FastAPI, asyncio, Pydantic, SQLAlchemy, and pytest. Always uses type hints, writes async-first, and returns runnable code.

### `nodejs-developer`
Senior Node.js developer. Builds APIs, background workers, and CLI tools. Uses modern ES modules, async/await, and covers error handling and rate limiting.

### `code-reviewer`
Expert code reviewer. Focuses on security vulnerabilities, performance issues, code quality, and best practices. Returns structured feedback with severity levels.

---

## Writing a Custom Skill

1. Create a new `.md` file in `skills/`:

```markdown
---
name: go-developer
description: Senior Go developer for building high-performance services and CLIs
---
You are a senior Go developer with expertise in net/http, goroutines, channels,
and the standard library.

## Responsibilities
- Write idiomatic Go code following effective Go guidelines
- Design concurrent systems using goroutines and channels
- Handle errors explicitly — never ignore them

## Standards
- Always use `context.Context` for cancellation
- Write table-driven tests
- Return errors, don't panic

## Output Format
Return complete, compilable Go code with package declarations and imports.
```

2. Restart the MCP server — skills are loaded from disk on startup.

3. _(Optional)_ Seed into Synatyx for RAG routing:
```bash
python scripts/seed_skills.py
```

---

## How Routing Works

When `skill_name` is **not** provided:

1. Synatyx RAG search — embeds the task and finds the closest skill by semantic similarity
2. Local fallback — if Synatyx is unavailable, scans `skills/` and keyword-matches against descriptions
3. Default — if nothing matches, uses the first skill alphabetically

When `skill_name` **is** provided:

1. Exact match in local `skills/` directory
2. Synatyx lookup by name if not found locally

---

## Skill Tips

- **Descriptions matter** — the description is what RAG embeds. Make it specific and keyword-rich.
- **Output format section** — always tell the skill how to format its response. Sub-agents with `enable_tools=true` should be told to use `write_file` for any code they produce.
- **Keep roles narrow** — a focused skill outperforms a general one every time.

