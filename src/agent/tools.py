"""
Sub-agent tools: file system and shell capabilities.

All file operations are sandboxed to agent_workspace (config).
Tools are defined in both Anthropic and OpenAI schema formats.
"""
import subprocess
from pathlib import Path
from src.core.config import settings


# ---------------------------------------------------------------------------
# Executors
# ---------------------------------------------------------------------------

def _resolve(path: str) -> Path:
    """Resolve path relative to workspace, prevent traversal."""
    workspace = Path(settings.agent_workspace).resolve()
    target = (workspace / path).resolve()
    if not str(target).startswith(str(workspace)):
        raise PermissionError(f"Path '{path}' escapes the agent workspace.")
    return target


def write_file(path: str, content: str) -> str:
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"


def read_file(path: str) -> str:
    target = _resolve(path)
    if not target.exists():
        return f"Error: file '{path}' does not exist."
    return target.read_text(encoding="utf-8")


def list_directory(path: str = ".") -> str:
    target = _resolve(path)
    if not target.exists():
        return f"Error: directory '{path}' does not exist."
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
    lines = [f"{'DIR ' if e.is_dir() else 'FILE'} {e.name}" for e in entries]
    return "\n".join(lines) if lines else "(empty)"


def run_command(command: str) -> str:
    workspace = Path(settings.agent_workspace).resolve()
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

TOOL_EXECUTORS = {
    "write_file": lambda args: write_file(args["path"], args["content"]),
    "read_file": lambda args: read_file(args["path"]),
    "list_directory": lambda args: list_directory(args.get("path", ".")),
    "run_command": lambda args: run_command(args["command"]),
}


def execute_tool(name: str, args: dict) -> str:
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return f"Error: unknown tool '{name}'."
    try:
        return executor(args)
    except Exception as e:
        return f"Error executing {name}: {e}"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

ANTHROPIC_TOOLS = [
    {
        "name": "write_file",
        "description": "Write content to a file inside the agent workspace. Creates parent directories if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace (e.g. 'src/hello.py')"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the content of a file inside the agent workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and directories inside the agent workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path relative to workspace (default: '.')"},
            },
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command in the agent workspace. Timeout: 30s.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
]

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in ANTHROPIC_TOOLS
]

