"""LLM factory – returns a chat model based on configured provider."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.config import Settings, get_settings


def get_llm(settings: Settings | None = None) -> BaseChatModel:
    s = settings or get_settings()

    provider = s.llm_provider.lower()
    if provider in ("gemini", "google"):
        provider = "google_genai"

    model_map = {
        "openai": s.openai_model,
        "anthropic": s.anthropic_model,
        "google_genai": s.google_model,
    }
    key_map = {
        "openai": s.openai_api_key,
        "anthropic": s.anthropic_api_key,
        "google_genai": s.google_api_key,
    }

    return init_chat_model(
        model=model_map[provider],
        model_provider=provider,
        temperature=s.llm_temperature,
        api_key=key_map[provider],
    )
