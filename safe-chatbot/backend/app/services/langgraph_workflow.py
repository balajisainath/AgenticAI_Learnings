from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.core.config import Settings
from app.domain.schemas import (
    ChatRequest,
    ChatResponse,
    GraphEdge,
    GraphNode,
    GraphResponse,
    GuardrailsInfo,
    TraceStep,
)
from app.services.guardrails_service import GuardrailsService


class ChatState(TypedDict, total=False):
    message: str
    history: list[dict[str, str]]
    session_id: str
    response: str
    guardrails_info: dict
    trace: list[dict[str, str]]


class SafeChatWorkflow:
    def __init__(self, settings: Settings, guardrails: GuardrailsService) -> None:
        self.settings = settings
        self.guardrails = guardrails
        self.graph = self._build_graph()

    async def run_async(self, request: ChatRequest) -> ChatResponse:
        initial: ChatState = {
            "message": request.message,
            "history": [m.model_dump() for m in request.history],
            "session_id": request.session_id,
            "trace": [],
        }
        result: ChatState = await self.graph.ainvoke(initial)

        guardrails_dict = result.get("guardrails_info", {})
        guardrails = GuardrailsInfo(**guardrails_dict) if guardrails_dict else GuardrailsInfo()
        trace = [TraceStep(**t) for t in result.get("trace", [])]

        return ChatResponse(
            message=result.get("response", ""),
            session_id=result.get("session_id", ""),
            guardrails=guardrails,
            trace=trace,
            metadata={
                "provider": self.settings.normalized_provider,
                "model": self.settings.selected_model_name,
                "nemo": str(guardrails.nemo.active),
                "guardrails_ai": str(guardrails.guardrails_ai.active),
            },
        )

    def export_graph_definition(self) -> GraphResponse:
        return GraphResponse(
            title="SafeBot Dual-Layer Guardrails Workflow",
            nodes=[
                GraphNode(id="input",       label="User Input",              x=0,    y=0),
                GraphNode(id="grails_in",   label="Guardrails AI Input",     x=200,  y=0),
                GraphNode(id="nemo_in",     label="NeMo Input Rails",        x=400,  y=0),
                GraphNode(id="llm",         label="LLM Generation",          x=600,  y=0),
                GraphNode(id="grails_out",  label="Guardrails AI Output",    x=800,  y=0),
                GraphNode(id="output",      label="Safe Response",           x=1000, y=0),
            ],
            edges=[
                GraphEdge(source="input",      target="grails_in"),
                GraphEdge(source="grails_in",  target="nemo_in"),
                GraphEdge(source="nemo_in",    target="llm"),
                GraphEdge(source="llm",        target="grails_out"),
                GraphEdge(source="grails_out", target="output"),
            ],
        )

    def _build_graph(self):
        builder: StateGraph = StateGraph(ChatState)
        builder.add_node("process_with_guardrails", self._process_node)
        builder.add_node("finalize", self._finalize_node)
        builder.set_entry_point("process_with_guardrails")
        builder.add_edge("process_with_guardrails", "finalize")
        builder.add_edge("finalize", END)
        return builder.compile()

    async def _process_node(self, state: ChatState) -> ChatState:
        trace = list(state.get("trace", []))
        trace.append({
            "node": "guardrails_pipeline",
            "detail": "Running dual-layer safety pipeline: Guardrails AI → NeMo → LLM → Guardrails AI output",
        })
        response, guardrails = await self.guardrails.process(
            message=state["message"],
            history=state.get("history", []),
        )
        if guardrails.input_blocked:
            trace.append({
                "node": "guardrails_pipeline",
                "detail": f"Input BLOCKED — reason: {(guardrails.block_reason or '')[:120]}",
            })
        elif guardrails.output_filtered:
            trace.append({"node": "guardrails_pipeline", "detail": "Output filtered/redacted by Guardrails AI output guard."})
        else:
            trace.append({"node": "guardrails_pipeline", "detail": "All safety checks passed — response delivered."})

        return {
            **state,
            "response": response,
            "guardrails_info": guardrails.model_dump(),
            "trace": trace,
        }

    async def _finalize_node(self, state: ChatState) -> ChatState:
        trace = list(state.get("trace", []))
        trace.append({"node": "finalize", "detail": "Response finalised and ready to deliver."})
        return {**state, "trace": trace}
