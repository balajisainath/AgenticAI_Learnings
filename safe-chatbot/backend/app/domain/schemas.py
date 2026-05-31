from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request / Response schemas ───────────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = ""
    history: list[HistoryMessage] = []
    provider: str = "openai"
    guardrails_ai_enabled: bool = True
    nemo_enabled: bool = True


# ── Per-framework layer metadata ─────────────────────────────────────────────

class GuardrailsAIInfo(BaseModel):
    """Metadata from the Guardrails AI (guardrails-ai) validation layer."""
    active: bool = False
    input_passed: bool = True
    input_blocked: bool = False
    output_passed: bool = True
    output_filtered: bool = False
    failed_validators: list[str] = []
    error_message: str | None = None


class NemoInfo(BaseModel):
    """Metadata from the NVIDIA NeMo Guardrails (Colang) layer."""
    active: bool = False
    input_checked: bool = False
    input_blocked: bool = False
    output_checked: bool = False
    rails_triggered: list[str] = []
    block_reason: str | None = None


# ── Combined guardrails metadata ─────────────────────────────────────────────

class GuardrailsInfo(BaseModel):
    """Aggregated safety metadata returned for every chat response."""
    # overall verdict
    input_blocked: bool = False
    output_filtered: bool = False
    block_reason: str | None = None
    # per-framework details
    guardrails_ai: GuardrailsAIInfo = GuardrailsAIInfo()
    nemo: NemoInfo = NemoInfo()


# ── Trace ────────────────────────────────────────────────────────────────────

class TraceStep(BaseModel):
    node: str
    detail: str


# ── Chat response ─────────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    message: str
    session_id: str
    guardrails: GuardrailsInfo
    trace: list[TraceStep]
    metadata: dict[str, str]


# ── Workflow graph (for visualisation) ───────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    x: float = 0.0
    y: float = 0.0


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphResponse(BaseModel):
    title: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
