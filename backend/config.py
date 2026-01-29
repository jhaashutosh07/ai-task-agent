from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
import os
import secrets


class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: Literal["openai", "ollama", "anthropic", "gemini"] = Field(default="openai")

    # OpenAI Settings
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    # Anthropic Settings
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")

    # Google Gemini Settings
    google_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-pro")

    # Ollama Settings
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2")

    # Multi-Provider Settings
    fallback_chain: list[str] = Field(default=["openai", "anthropic", "gemini", "ollama"])

    # Agent Settings
    max_iterations: int = Field(default=15)
    max_parallel_tools: int = Field(default=3)
    workspace_path: str = Field(default="./workspace")
    enable_human_confirmation: bool = Field(default=True)
    dangerous_actions: list[str] = Field(default=["shell_execute", "file_delete", "send_email"])

    # Memory Settings
    memory_db_path: str = Field(default="./data/memory.db")
    vector_db_path: str = Field(default="./data/vectordb")
    max_memory_items: int = Field(default=1000)

    # Workflow Settings
    workflows_path: str = Field(default="./data/workflows")
    max_workflow_steps: int = Field(default=50)

    # Server Settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # Authentication Settings
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    auth_db_path: str = Field(default=os.environ.get("AUTH_DB_PATH", "./data/auth.db"))

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)
    rate_limit_burst: int = Field(default=10)

    # Email Settings (optional)
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")

    # Sandbox Settings
    enable_sandbox: bool = Field(default=True)
    sandbox_timeout: int = Field(default=30)
    sandbox_memory_limit: str = Field(default="256m")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
