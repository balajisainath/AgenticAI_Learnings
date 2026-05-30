from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Prompt Schemas ---
class PromptCreate(BaseModel):
    name: str
    description: str = ""


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PromptResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    version_count: int = 0
    latest_version: Optional[int] = None


# --- Version Schemas ---
class VersionCreate(BaseModel):
    system_prompt: str = ""
    user_prompt_template: str
    model: str = ""
    temperature: float = 0.7
    notes: str = ""


class VersionResponse(BaseModel):
    id: str
    prompt_id: str
    version_number: int
    system_prompt: str
    user_prompt_template: str
    model: str
    temperature: float
    notes: str
    created_at: str


# --- Test Case Schemas ---
class TestCaseCreate(BaseModel):
    name: str
    variables: dict = {}


class TestCaseResponse(BaseModel):
    id: str
    prompt_id: str
    name: str
    variables: dict
    created_at: str


# --- Run Schemas ---
class RunRequest(BaseModel):
    version_id: str
    input_text: str
    variables: dict = {}
    model: str = ""
    temperature: float = 0.7


class RunResponse(BaseModel):
    id: str
    version_id: str
    test_case_id: Optional[str] = None
    input_text: str
    variables: dict
    output_text: str
    model_used: str
    temperature: float
    latency_ms: int
    token_count: int
    rating: int
    notes: str
    created_at: str


class RateRunRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    notes: str = ""


# --- Comparison Schemas ---
class CompareRequest(BaseModel):
    prompt_id: str
    version_ids: list[str]
    input_text: str
    variables: dict = {}
    model: str = ""
    temperature: float = 0.7


class CompareResult(BaseModel):
    version_id: str
    version_number: int
    output_text: str
    latency_ms: int
    token_count: int


class CompareResponse(BaseModel):
    id: str
    name: str
    prompt_id: str
    version_ids: list[str]
    input_text: str
    variables: dict
    results: list[CompareResult]
    created_at: str


# --- Stats ---
class VersionStats(BaseModel):
    version_id: str
    version_number: int
    total_runs: int
    avg_rating: float
    avg_latency_ms: float
    avg_tokens: float


class PromptStats(BaseModel):
    prompt_id: str
    prompt_name: str
    versions: list[VersionStats]
