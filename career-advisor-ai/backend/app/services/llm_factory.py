import importlib
import os
from typing import Any
from urllib.parse import urlparse

from app.core.config import Settings


def _valid_base_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return cleaned


def build_chat_model(settings: Settings) -> Any | None:
    chat_models_module = importlib.import_module("langchain.chat_models")
    init_chat_model = getattr(chat_models_module, "init_chat_model")
    provider = settings.normalized_provider

    if provider == "openai":
        if not settings.openai_api_key:
            return None

        # Prevent empty/invalid env values from breaking the OpenAI SDK default base URL resolution.
        sanitized_base_url = _valid_base_url(settings.openai_base_url)
        if sanitized_base_url is None and os.environ.get("OPENAI_BASE_URL", "").strip() == "":
            os.environ.pop("OPENAI_BASE_URL", None)

        kwargs: dict[str, str | float] = {
            "temperature": settings.llm_temperature,
            "api_key": settings.openai_api_key,
        }
        if sanitized_base_url:
            kwargs["base_url"] = sanitized_base_url
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
