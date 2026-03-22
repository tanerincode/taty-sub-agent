# 🔧 Sub-agent Tools

When `enable_tools=true` (the default), sub-agents run a live tool-calling loop and have access to the following tools. All file operations are sandboxed to `AGENT_WORKSPACE` (defaults to the project root).

---

## write_file

Write content to a file. Parent directories are created automatically.

| Argument | Type | Description |
|---|---|---|
| `path` | string | File path relative to workspace (e.g. `src/hello.py`) |
| `content` | string | Full file content to write |

**Example (model call):**
```json
{
  "name": "write_file",
  "input": {
    "path": "src/hello.py",
    "content": "def hello() -> str:\n    return 'Hello, World!'\n"
  }
}
```

**Returns:** `Written N bytes to src/hello.py`

---

## read_file

Read the content of an existing file.

| Argument | Type | Description |
|---|---|---|
| `path` | string | File path relative to workspace |

**Returns:** Full file content as a string, or an error message if the file doesn't exist.

---

## list_directory

List files and directories at a given path.

| Argument | Type | Default | Description |
|---|---|---|---|
| `path` | string | `.` | Directory path relative to workspace |

**Returns:**
```
DIR  src
DIR  tests
FILE hello-world.py
FILE main.py
FILE pyproject.toml
```

---

## run_command

Execute a shell command in the agent workspace. Has a 30-second timeout.

| Argument | Type | Description |
|---|---|---|
| `command` | string | Shell command to run |

**Example:**
```json
{ "name": "run_command", "input": { "command": "python -m pytest tests/ -v" } }
```

**Returns:** Combined stdout + stderr, or a timeout/error message.

> ⚠️ **Be careful** — `run_command` can execute arbitrary shell commands. Only enable it for tasks where you trust the sub-agent to run code.

---

## Security

- All `write_file`, `read_file`, and `list_directory` calls are validated to ensure the resolved path stays inside `AGENT_WORKSPACE`. Path traversal (e.g. `../../etc/passwd`) is rejected with a `PermissionError`.
- `run_command` runs in `AGENT_WORKSPACE` as the current user with a 30s timeout.
- Set `enable_tools=false` when you only need a text response and want to avoid any file system access.

---

## Disabling tools

Pass `enable_tools=false` to any `invoke_agent` or task in `invoke_parallel`:

```
invoke_agent(
  task="Explain Python decorators",
  skill_name="python-developer",
  enable_tools=false
)
```

The sub-agent will respond with text only and cannot touch the file system.

