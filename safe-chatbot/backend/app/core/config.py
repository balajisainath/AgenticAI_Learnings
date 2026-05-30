from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SafeBot API"
    app_env: str = "development"
    allowed_origins: str = "http://localhost:5173"

    llm_provider: str = "openai"
    llm_temperature: float = 0.4

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"

    google_api_key: str | None = None
    google_model: str = "gemini-2.0-flash"

    @property
    def normalized_provider(self) -> str:
        provider = self.llm_provider.strip().lower()
        alias_map = {
            "gemini": "google_genai",
            "google": "google_genai",
            "claude": "anthropic",
            "gpt": "openai",
        }
        return alias_map.get(provider, provider)

    @property
    def selected_model_name(self) -> str:
        provider = self.normalized_provider
        if provider == "anthropic":
            return self.anthropic_model
        if provider == "google_genai":
            return self.google_model
        return self.openai_model

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
