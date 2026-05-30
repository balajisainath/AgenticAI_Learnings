import importlib
from typing import Any

from app.core.config import Settings


def build_chat_model(settings: Settings, model_override: str = "", temperature_override: float | None = None) -> Any | None:
    chat_models_module = importlib.import_module("langchain.chat_models")
    init_chat_model = getattr(chat_models_module, "init_chat_model")
    provider = settings.normalized_provider
    temperature = temperature_override if temperature_override is not None else settings.llm_temperature

    if model_override:
        # Determine provider from model name
        if "gpt" in model_override or "o1" in model_override or "o3" in model_override:
            provider = "openai"
        elif "claude" in model_override:
            provider = "anthropic"
        elif "gemini" in model_override:
            provider = "google_genai"

    if provider == "openai":
        if not settings.openai_api_key:
            return None
        kwargs: dict[str, Any] = {
            "temperature": temperature,
            "api_key": settings.openai_api_key,
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return init_chat_model(
            model_override or settings.openai_model,
            model_provider="openai",
            **kwargs,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            return None
        return init_chat_model(
            model_override or settings.anthropic_model,
            model_provider="anthropic",
            temperature=temperature,
            api_key=settings.anthropic_api_key,
        )

    if provider == "google_genai":
        if not settings.google_api_key:
            return None
        return init_chat_model(
            model_override or settings.google_model,
            model_provider="google_genai",
            temperature=temperature,
            api_key=settings.google_api_key,
        )

    return None
