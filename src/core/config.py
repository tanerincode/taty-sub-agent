from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_FILE, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # Anthropic
    anthropic_api_key: str = ""
    default_model: str = "claude-sonnet-4-6"

    # OpenAI
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o"

    max_parallel_agents: int = 5
    max_tokens: int = 8096

    # Synatyx
    synatyx_user_id: str = "tombastaner"
    synatyx_project: str = "taty-sub-agent"

    # Skills directory (local) — absolute path derived from project root
    skills_dir: str = str(Path(__file__).resolve().parents[2] / "skills")

    # Workspace for sub-agent file tools (write_file, read_file, etc.)
    agent_workspace: str = str(Path(__file__).resolve().parents[2])


settings = Settings()
