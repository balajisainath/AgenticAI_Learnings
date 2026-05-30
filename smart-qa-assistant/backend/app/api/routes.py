from functools import lru_cache

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.domain.schemas import (
    AskRequest,
    AskResponse,
    CompareRequest,
    CompareResponse,
    GraphResponse,
)
from app.services.langgraph_workflow import SmartQAWorkflow

router = APIRouter(prefix="/api/v1", tags=["smart-qa"])


@lru_cache
def get_workflow() -> SmartQAWorkflow:
    settings = get_settings()
    return SmartQAWorkflow(settings)


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.post("/chat/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    workflow: SmartQAWorkflow = Depends(get_workflow),
) -> AskResponse:
    return workflow.run(payload)


@router.post("/chat/compare", response_model=CompareResponse)
def compare_techniques(
    payload: CompareRequest,
    workflow: SmartQAWorkflow = Depends(get_workflow),
) -> CompareResponse:
    responses = []
    for technique in payload.techniques:
        request = AskRequest(
            question=payload.question,
            persona=payload.persona,
            style=payload.style,
            technique=technique,
        )
        responses.append(workflow.run(request))

    return CompareResponse(
        question=payload.question,
        persona=payload.persona,
        style=payload.style,
        responses=responses,
    )


@router.get("/graph", response_model=GraphResponse)
def get_graph(workflow: SmartQAWorkflow = Depends(get_workflow)) -> GraphResponse:
    return workflow.export_graph_definition()
