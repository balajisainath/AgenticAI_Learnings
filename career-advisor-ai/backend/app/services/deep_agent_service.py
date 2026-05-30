from __future__ import annotations

from typing import Any, Literal

from app.core.config import Settings
from app.services.knowledge_base import CareerKnowledgeBase


class DeepAgentService:
    def __init__(self, settings: Settings, knowledge_base: CareerKnowledgeBase) -> None:
        self.settings = settings
        self.knowledge_base = knowledge_base
        self._agent: Any | None = None
        self._agent_error: str | None = None

    @property
    def enabled(self) -> bool:
        return self.settings.deep_agent_enabled

    def _get_agent(self) -> Any | None:
        if not self.settings.deep_agent_enabled:
            self._agent_error = "Deep agent is disabled by configuration."
            return None

        if self._agent is not None:
            return self._agent

        try:
            from deepagents import create_deep_agent  # type: ignore
        except Exception as exc:  # pragma: no cover - runtime optional dependency
            self._agent_error = f"deepagents import failed: {exc}"
            return None

        search_tool = self._build_search_tool()

        try:
            self._agent = create_deep_agent(
                model=self.settings.deep_agent_model,
                tools=[search_tool],
                system_prompt=(
                    "You are a market-aware career intelligence agent. "
                    "Research job trends, skills, and learning resources using the available tools. "
                    "Return concise, source-grounded insights only."
                ),
                subagents=[
                    {
                        "name": "market-researcher",
                        "description": "Researches role demand and skill trends.",
                        "system_prompt": (
                            "You are a deep researcher for technology careers. Use tools to gather evidence, "
                            "then summarize key trends in a short format with source links."
                        ),
                        "tools": [search_tool],
                    },
                    {
                        "name": "learning-curator",
                        "description": "Finds practical learning paths and certifications.",
                        "system_prompt": (
                            "You curate practical learning resources and certifications. Prioritize actionable content."
                        ),
                        "tools": [search_tool],
                    },
                ],
            )
            self._agent_error = None
            return self._agent
        except Exception as exc:  # pragma: no cover - provider/runtime variability
            self._agent_error = f"deep agent initialization failed: {exc}"
            return None

    def _build_search_tool(self):
        tavily_key = self.settings.tavily_api_key

        if tavily_key:
            try:
                from tavily import TavilyClient  # type: ignore

                tavily_client = TavilyClient(api_key=tavily_key)

                def internet_search(
                    query: str,
                    max_results: int = 5,
                    topic: Literal["general", "news", "finance"] = "general",
                ) -> dict[str, Any]:
                    """Search external web sources for career market intelligence."""
                    return tavily_client.search(query=query, max_results=max_results, topic=topic)

                return internet_search
            except Exception:
                pass

        def local_knowledge_search(query: str, max_results: int = 5) -> dict[str, Any]:
            """Search local career knowledge base when web search is unavailable."""
            docs = self.knowledge_base.retrieve(query, limit=max_results)
            return {
                "query": query,
                "results": [
                    {
                        "title": item.item.title,
                        "url": item.item.url,
                        "snippet": item.item.content[:220],
                        "score": round(item.score, 3),
                    }
                    for item in docs
                ],
            }

        return local_knowledge_search

    def research(self, query: str, session_id: str | None = None) -> dict[str, Any]:
        agent = self._get_agent()
        if agent is None:
            docs = self.knowledge_base.retrieve(query, limit=4)
            summary = "\n".join(
                [
                    "Deep agent fallback (local retrieval mode):",
                    "- Deep agent package, API key, or runtime is unavailable.",
                    "- Showing top local context to keep project fully usable.",
                ]
            )
            return {
                "summary": summary,
                "sources": [entry.item.url for entry in docs],
                "used_deep_agent": False,
                "metadata": {
                    "session_id": session_id or "none",
                    "status": self._agent_error or "fallback",
                },
            }

        prompt = (
            "Research this career question and return concise output with bullets and source URLs.\n\n"
            f"Question: {query}\n\n"
            "Output sections:\n"
            "1) Market signals\n"
            "2) Critical skills\n"
            "3) Learning path suggestions\n"
            "4) Sources"
        )

        result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        messages = result.get("messages", [])
        final_message = messages[-1].content if messages else "No deep-agent response was produced."
        text = final_message if isinstance(final_message, str) else str(final_message)

        source_lines = [line.strip("- ") for line in text.splitlines() if "http" in line]

        return {
            "summary": text,
            "sources": source_lines,
            "used_deep_agent": True,
            "metadata": {
                "session_id": session_id or "none",
                "model": self.settings.deep_agent_model,
                "mode": "deep-agent",
            },
        }
