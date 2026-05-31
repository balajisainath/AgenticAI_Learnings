from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.core.config import Settings
from app.domain.schemas import (
    AskRequest,
    AskResponse,
    GraphResponse,
    PromptTechnique,
    TraceStep,
)
from app.prompts.few_shot import FEW_SHOT_EXAMPLES
from app.prompts.personas import PERSONA_INSTRUCTIONS
from app.prompts.styles import STYLE_INSTRUCTIONS, TECHNIQUE_INSTRUCTIONS
from app.services.llm_factory import build_chat_model


class WorkflowState(TypedDict, total=False):
    question: str
    persona: str
    style: str
    requested_technique: str
    selected_technique: str
    role_instruction: str
    style_instruction: str
    few_shots: list[dict[str, str]]
    prompt_messages: list[BaseMessage]
    prompt_preview: str
    raw_response: str
    formatted_response: str
    trace: list[dict[str, str]]


def _append_trace(state: WorkflowState, node: str, detail: str) -> list[dict[str, str]]:
    trace = list(state.get("trace", []))
    trace.append({"node": node, "detail": detail})
    return trace


class SmartQAWorkflow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = build_chat_model(settings)
        self.graph = self._build_graph()

    def run(self, request: AskRequest) -> AskResponse:
        initial_state: WorkflowState = {
            "question": request.question,
            "persona": request.persona.value,
            "style": request.style.value,
            "requested_technique": request.technique.value,
            "trace": [],
        }
        result = self.graph.invoke(initial_state)

        selected = PromptTechnique(result["selected_technique"])
        trace = [TraceStep(**item) for item in result.get("trace", [])]

        metadata = {
            "persona": request.persona.value,
            "style": request.style.value,
            "provider": self.settings.normalized_provider,
            "model": self.settings.selected_model_name if self.model else "mock-llm",
        }
        return AskResponse(
            technique=selected,
            answer=result["formatted_response"],
            prompt_preview=result.get("prompt_preview", ""),
            trace=trace,
            metadata=metadata,
        )

    def run_streaming(self, request: AskRequest):
        """Stream node-by-node execution events via LangGraph's .stream()."""
        import time

        initial_state: WorkflowState = {
            "question": request.question,
            "persona": request.persona.value,
            "style": request.style.value,
            "requested_technique": request.technique.value,
            "trace": [],
        }

        metadata = {
            "persona": request.persona.value,
            "style": request.style.value,
            "provider": self.settings.normalized_provider,
            "model": self.settings.selected_model_name if self.model else "mock-llm",
        }

        final_state: WorkflowState = {}

        for chunk in self.graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                if not isinstance(node_output, dict):
                    continue

                final_state.update(node_output)

                trace_entries = node_output.get("trace", [])
                latest_trace = trace_entries[-1] if trace_entries else {}

                event = {
                    "type": "node_start" if node_name != "response_formatter" else "node_complete",
                    "node": node_name,
                    "detail": latest_trace.get("detail", ""),
                    "timestamp": time.time(),
                }

                if node_name == "prompt_builder":
                    event["prompt_preview"] = node_output.get("prompt_preview", "")

                if node_name == "response_formatter":
                    event["type"] = "complete"
                    selected = PromptTechnique(final_state.get("selected_technique", "auto"))
                    event["result"] = {
                        "technique": selected.value,
                        "answer": node_output.get("formatted_response", ""),
                        "prompt_preview": final_state.get("prompt_preview", ""),
                        "trace": final_state.get("trace", []),
                        "metadata": metadata,
                    }

                yield event
                # Stagger events so the frontend can render nodes lighting up sequentially
                time.sleep(0.35)

    def export_graph_definition(self) -> GraphResponse:
        return GraphResponse(
            title="Smart Prompting Workflow",
            nodes=[
                {"id": "strategy_selector", "label": "Select Strategy", "x": 80, "y": 90},
                {"id": "role_injector", "label": "Inject Role", "x": 280, "y": 90},
                {"id": "few_shot_loader", "label": "Load Few-Shot", "x": 480, "y": 90},
                {"id": "prompt_builder", "label": "Build Prompt", "x": 680, "y": 90},
                {"id": "llm_invoker", "label": "Invoke LLM", "x": 880, "y": 90},
                {"id": "response_formatter", "label": "Format Response", "x": 1080, "y": 90},
            ],
            edges=[
                {"source": "strategy_selector", "target": "role_injector"},
                {"source": "role_injector", "target": "few_shot_loader"},
                {"source": "few_shot_loader", "target": "prompt_builder"},
                {"source": "prompt_builder", "target": "llm_invoker"},
                {"source": "llm_invoker", "target": "response_formatter"},
            ],
        )

    def _select_strategy(self, state: WorkflowState) -> WorkflowState:
        requested = state["requested_technique"]
        if requested != PromptTechnique.auto.value:
            selected = requested
        else:
            question = state["question"].lower()
            if any(word in question for word in ["big picture", "principle", "framework", "tradeoff"]):
                selected = PromptTechnique.step_back.value
            elif any(word in question for word in ["improve", "review", "refine", "weakness"]):
                selected = PromptTechnique.critique_refine.value
            elif any(word in question for word in ["confidence", "uncertain", "risky", "best option"]):
                selected = PromptTechnique.self_consistency.value
            elif any(word in question for word in ["why", "debug", "step", "plan"]):
                selected = PromptTechnique.chain_of_thought.value
            elif any(word in question for word in ["example", "template", "sample"]):
                selected = PromptTechnique.few_shot.value
            elif len(question) < 120:
                selected = PromptTechnique.role.value
            else:
                selected = PromptTechnique.zero_shot.value

        return {
            "selected_technique": selected,
            "trace": _append_trace(
                state,
                "strategy_selector",
                f"Requested={requested}, selected={selected}",
            ),
        }

    def _inject_role(self, state: WorkflowState) -> WorkflowState:
        persona_key = state["persona"]
        style_key = state["style"]

        role_instruction = PERSONA_INSTRUCTIONS.get(
            persona_key,
            "You are a practical assistant focused on correctness and clarity.",
        )
        style_instruction = STYLE_INSTRUCTIONS.get(
            style_key,
            "Answer clearly with relevant technical details.",
        )

        return {
            "role_instruction": role_instruction,
            "style_instruction": style_instruction,
            "trace": _append_trace(
                state,
                "role_injector",
                f"Persona={persona_key}, style={style_key}",
            ),
        }

    def _load_few_shot(self, state: WorkflowState) -> WorkflowState:
        selected = PromptTechnique(state["selected_technique"])
        examples = FEW_SHOT_EXAMPLES.get(selected, [])

        return {
            "few_shots": examples,
            "trace": _append_trace(
                state,
                "few_shot_loader",
                f"Loaded {len(examples)} examples",
            ),
        }

    def _build_prompt(self, state: WorkflowState) -> WorkflowState:
        selected = PromptTechnique(state["selected_technique"])
        messages: list[BaseMessage] = []

        system_text = "\n".join(
            [
                "You are Smart Q&A Assistant.",
                state["role_instruction"],
                state["style_instruction"],
                TECHNIQUE_INSTRUCTIONS[selected],
                "Keep answers factual, transparent about assumptions, and easy to scan.",
            ]
        )
        messages.append(SystemMessage(content=system_text))

        for example in state.get("few_shots", []):
            messages.append(HumanMessage(content=example["input"]))
            messages.append(AIMessage(content=example["output"]))

        messages.append(HumanMessage(content=state["question"]))

        preview_parts: list[str] = []
        for message in messages:
            role = message.type.upper()
            preview_parts.append(f"[{role}] {message.content}")
        prompt_preview = "\n\n".join(preview_parts)[:1800]

        return {
            "prompt_messages": messages,
            "prompt_preview": prompt_preview,
            "trace": _append_trace(
                state,
                "prompt_builder",
                f"Built prompt with {len(messages)} messages",
            ),
        }

    def _invoke_llm(self, state: WorkflowState) -> WorkflowState:
        if not self.model:
            selected = state["selected_technique"].replace("_", " ").title()
            answer = (
                f"[Mock LLM] Strategy: {selected}\n\n"
                f"Question: {state['question']}\n\n"
                "Set provider API key in backend/.env (OPENAI_API_KEY, ANTHROPIC_API_KEY, or "
                "GOOGLE_API_KEY) to enable live model answers. "
                "The workflow and prompt engineering pipeline are fully active."
            )
            trace_detail = "Returned deterministic mock response"
        else:
            response = self.model.invoke(state["prompt_messages"])
            if isinstance(response.content, str):
                answer = response.content
            else:
                answer = "\n".join(str(item) for item in response.content)
            trace_detail = (
                f"Invoked {self.settings.normalized_provider}:{self.settings.selected_model_name}"
            )

        return {
            "raw_response": answer,
            "trace": _append_trace(state, "llm_invoker", trace_detail),
        }

    def _format_response(self, state: WorkflowState) -> WorkflowState:
        selected = state["selected_technique"].replace("_", " ").title()
        formatted = (
            f"Technique Used: {selected}\n\n"
            f"{state['raw_response'].strip()}\n\n"
            "Response generated via LangGraph prompt workflow."
        )

        return {
            "formatted_response": formatted,
            "trace": _append_trace(state, "response_formatter", "Applied response formatting"),
        }

    def _build_graph(self) -> Any:
        graph = StateGraph(WorkflowState)

        graph.add_node("strategy_selector", self._select_strategy)
        graph.add_node("role_injector", self._inject_role)
        graph.add_node("few_shot_loader", self._load_few_shot)
        graph.add_node("prompt_builder", self._build_prompt)
        graph.add_node("llm_invoker", self._invoke_llm)
        graph.add_node("response_formatter", self._format_response)

        graph.set_entry_point("strategy_selector")
        graph.add_edge("strategy_selector", "role_injector")
        graph.add_edge("role_injector", "few_shot_loader")
        graph.add_edge("few_shot_loader", "prompt_builder")
        graph.add_edge("prompt_builder", "llm_invoker")
        graph.add_edge("llm_invoker", "response_formatter")
        graph.add_edge("response_formatter", END)

        return graph.compile()
