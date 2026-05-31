"""LLM factory – instantiate the configured LLM provider."""

from langchain_core.language_models import BaseChatModel

from app.config import get_settings


def get_llm() -> BaseChatModel:
    """Return a LangChain chat model based on settings."""
    settings = get_settings()

    match settings.llm_provider.lower():
        case "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.llm_temperature,
                api_key=settings.openai_api_key,
            )
        case "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=settings.anthropic_model,
                temperature=settings.llm_temperature,
                api_key=settings.anthropic_api_key,
            )
        case "google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=settings.google_model,
                temperature=settings.llm_temperature,
                google_api_key=settings.google_api_key,
            )
        case _:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
