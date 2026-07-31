from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
