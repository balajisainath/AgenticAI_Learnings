import importlib
from typing import Any

from app.core.config import Settings


def build_chat_model(settings: Settings) -> Any | None:
    chat_models_module = importlib.import_module("langchain.chat_models")
    init_chat_model = getattr(chat_models_module, "init_chat_model")
    provider = settings.normalized_provider

    if provider == "openai":
        if not settings.openai_api_key:
            return None
        kwargs: dict[str, Any] = {
            "temperature": settings.llm_temperature,
            "api_key": settings.openai_api_key,
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return init_chat_model(
            settings.openai_model,
            model_provider="openai",
            **kwargs,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            return None
        return init_chat_model(
            settings.anthropic_model,
            model_provider="anthropic",
            temperature=settings.llm_temperature,
            api_key=settings.anthropic_api_key,
        )

    if provider == "google_genai":
        if not settings.google_api_key:
            return None
        return init_chat_model(
            settings.google_model,
            model_provider="google_genai",
            temperature=settings.llm_temperature,
            api_key=settings.google_api_key,
        )

    return None
