from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    supervisor_model: str = "openai/gpt-5-nano"
    agent_model: str = "anthropic/claude-haiku-4.5"

    daily_budget_usd: float = 1.00
    max_cost_per_request_usd: float = 0.10

    # Where the UI's Live/Mock switch starts. Mock is forced when no API key is set.
    mock_llm: bool = False
    # Multiplies the scripted latencies in mock mode (0 makes tests instant).
    mock_latency_scale: float = 1.0

    wiki_user_agent: str = "FanDesk-Demo/1.0 (contact: not-set)"

    ipl_db_path: Path = Path("data/ipl.db")
    app_db_path: Path = Path("data/app.db")

    # OTLP/HTTP traces endpoint, e.g. http://phoenix:6006/v1/traces. Empty disables tracing.
    phoenix_collector_endpoint: str = ""
    phoenix_url: str = "http://localhost:6006"

    @property
    def live_available(self) -> bool:
        return bool(self.openrouter_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
