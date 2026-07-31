from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolves to the project root .env (two levels above backend/app/) so Settings()
# loads correctly whether run from backend/, the project root, or inside Docker
# (where env vars come from `env_file` in docker-compose.yml instead, and this
# path simply won't exist — pydantic-settings tolerates a missing env_file).
_PROJECT_ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # env_prefix is required here, not cosmetic: pydantic-settings gives real OS
    # environment variables priority over .env file values, and this machine has
    # OTHER projects (e.g. AgentForge) that set generic User-level env vars like
    # AZURE_OPENAI_ENDPOINT globally — those silently override an unprefixed .env
    # and point this app at the wrong Azure resource. Confirmed by hitting exactly
    # that collision live: this app's .env said one endpoint, Settings() loaded a
    # completely different one from a stray global AZURE_OPENAI_ENDPOINT.
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT_ENV, env_prefix="JOBASSISTANT_", extra="ignore"
    )

    llm_provider: str = "azure_openai"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = ""
    azure_openai_deployment: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"

    search_provider: str = "azure_bing"
    azure_bing_search_key: str = ""
    azure_bing_search_endpoint: str = ""
    google_custom_search_api_key: str = ""
    google_custom_search_cx: str = ""

    database_url: str = "sqlite:///./data/jobassistant.db"
    scheduler_hour: int = 7
    match_threshold: int = 85


settings = Settings()
