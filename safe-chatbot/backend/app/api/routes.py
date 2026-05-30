from functools import lru_cache

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.domain.schemas import ChatRequest, ChatResponse, GraphResponse
from app.services.guardrails_service import GuardrailsService
from app.services.langgraph_workflow import SafeChatWorkflow

router = APIRouter(prefix="/api/v1", tags=["safe-chatbot"])


# ── Singletons ────────────────────────────────────────────────────────────────

@lru_cache
def _get_guardrails_service() -> GuardrailsService:
    settings = get_settings()
    svc = GuardrailsService(settings)
    svc.initialize()
    return svc


@lru_cache
def _get_workflow() -> SafeChatWorkflow:
    settings = get_settings()
    guardrails = _get_guardrails_service()
    return SafeChatWorkflow(settings, guardrails)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    guardrails = _get_guardrails_service()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "guardrails": guardrails.status,
    }


@router.post("/chat/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    workflow: SafeChatWorkflow = Depends(_get_workflow),
) -> ChatResponse:
    return await workflow.run_async(payload)


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    workflow: SafeChatWorkflow = Depends(_get_workflow),
) -> GraphResponse:
    return workflow.export_graph_definition()


@router.get("/guardrails/status")
async def guardrails_status() -> dict:
    return _get_guardrails_service().status
