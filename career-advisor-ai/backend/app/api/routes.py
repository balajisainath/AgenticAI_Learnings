from functools import lru_cache

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.domain.schemas import (
    CareerAnalysisRequest,
    CareerAnalysisResponse,
    ChatRequest,
    ChatResponse,
    DeepResearchRequest,
    DeepResearchResponse,
    GraphResponse,
)
from app.services.deep_agent_service import DeepAgentService
from app.services.knowledge_base import CareerKnowledgeBase
from app.services.langgraph_workflow import CareerAdvisorWorkflow

router = APIRouter(prefix="/api/v1", tags=["career-advisor"])


@lru_cache
def get_workflow() -> CareerAdvisorWorkflow:
    settings = get_settings()
    return CareerAdvisorWorkflow(settings)


@lru_cache
def get_deep_agent_service() -> DeepAgentService:
    settings = get_settings()
    return DeepAgentService(settings, CareerKnowledgeBase())


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.post("/career/analyze", response_model=CareerAnalysisResponse)
def analyze_career(
    payload: CareerAnalysisRequest,
    workflow: CareerAdvisorWorkflow = Depends(get_workflow),
) -> CareerAnalysisResponse:
    return workflow.run(payload)


@router.post("/career/chat", response_model=ChatResponse)
def chat_career_coach(
    payload: ChatRequest,
    workflow: CareerAdvisorWorkflow = Depends(get_workflow),
) -> ChatResponse:
    return workflow.chat(payload)


@router.post("/career/deep-research", response_model=DeepResearchResponse)
def deep_research(
    payload: DeepResearchRequest,
    deep_agent: DeepAgentService = Depends(get_deep_agent_service),
) -> DeepResearchResponse:
    return DeepResearchResponse(**deep_agent.research(payload.query, payload.session_id))


@router.get("/career/graph", response_model=GraphResponse)
def get_graph(workflow: CareerAdvisorWorkflow = Depends(get_workflow)) -> GraphResponse:
    return workflow.export_graph_definition()
