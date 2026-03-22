# 🚀 Usage Guide

## invoke_agent

Run a single sub-agent on a task. The best skill is RAG-matched automatically, or you can pick one by name.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task` | string | required | What you want the sub-agent to do |
| `skill_name` | string | auto | Skill to use (e.g. `python-developer`) |
| `context` | string | — | Extra context injected into the system prompt |
| `provider` | string | `anthropic` | Model provider: `anthropic` or `openai` |
| `model` | string | default | Override model (e.g. `gpt-4o`, `claude-opus-4-6`) |
| `store_result` | bool | `true` | Persist result to Synatyx memory |
| `enable_tools` | bool | `true` | Give the sub-agent file + shell tools |

### Examples

**Auto-routed (RAG picks the best skill):**
```
invoke_agent(
  task="Write a FastAPI endpoint for user registration with JWT auth"
)
```

**Explicit skill:**
```
invoke_agent(
  task="Create hello-world.py with a function that returns 'Hello, World!'",
  skill_name="python-developer"
)
```

**With extra context:**
```
invoke_agent(
  task="Add rate limiting to the existing Express server",
  skill_name="nodejs-developer",
  context="The server is in src/server.js and uses the express framework"
)
```

**OpenAI provider:**
```
invoke_agent(
  task="Review this code for security issues: eval(user_input)",
  skill_name="code-reviewer",
  provider="openai",
  model="gpt-4o"
)
```

**Without tools (text output only):**
```
invoke_agent(
  task="Explain what a context manager is in Python",
  skill_name="python-developer",
  enable_tools=false
)
```

---

## invoke_parallel

Run multiple sub-agents concurrently. Concurrency is capped by `MAX_PARALLEL_AGENTS`.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tasks` | list | required | List of task objects (see below) |
| `batch_description` | string | — | Human-readable label for logging |

Each task object supports the same fields as `invoke_agent`: `task`, `skill_name`, `context`, `provider`, `model`, `store_result`, `enable_tools`.

### Example

```
invoke_parallel(
  tasks=[
    {
      "task": "Create a Python FastAPI health-check endpoint",
      "skill_name": "python-developer"
    },
    {
      "task": "Review src/auth.py for security vulnerabilities",
      "skill_name": "code-reviewer"
    },
    {
      "task": "Write a Node.js script to batch-process a CSV file",
      "skill_name": "nodejs-developer"
    }
  ],
  batch_description="Sprint kick-off tasks"
)
```

All three run at the same time. Results come back as a list in the same order.

---

## list_skills

Returns all available skills — from the local `skills/` directory.

```
list_skills()
```

Example response:
```json
[
  { "name": "python-developer", "description": "Senior Python developer...", "source": "local" },
  { "name": "nodejs-developer", "description": "Senior Node.js developer...", "source": "local" },
  { "name": "code-reviewer",    "description": "Expert code reviewer...",    "source": "local" }
]
```

---

## Tips

- **Let RAG route** — omitting `skill_name` lets Synatyx find the best skill via semantic search. It usually gets it right.
- **Use `context`** — tell the agent about existing files, frameworks, or constraints to get better output.
- **Use `invoke_parallel` aggressively** — independent tasks (write feature A + write feature B + write tests) run much faster in parallel.
- **`enable_tools=false`** — useful when you just want a text answer, not file creation.

