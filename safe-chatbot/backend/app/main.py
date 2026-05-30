from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly warm up the guardrails service on startup
    from app.api.routes import _get_guardrails_service
    _get_guardrails_service()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Safe chatbot with NVIDIA NeMo Guardrails + LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
