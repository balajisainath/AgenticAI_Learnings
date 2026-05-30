from enum import Enum

from pydantic import BaseModel, Field


class Persona(str, Enum):
    teacher = "teacher"
    architect = "architect"
    analyst = "analyst"
    product_coach = "product_coach"


class PromptTechnique(str, Enum):
    auto = "auto"
    zero_shot = "zero_shot"
    role = "role"
    few_shot = "few_shot"
    chain_of_thought = "chain_of_thought"
    step_back = "step_back"
    critique_refine = "critique_refine"
    self_consistency = "self_consistency"
    style_variation = "style_variation"


class PromptStyle(str, Enum):
    concise = "concise"
    technical = "technical"
    socratic = "socratic"
    executive = "executive"


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    persona: Persona = Persona.architect
    style: PromptStyle = PromptStyle.technical
    technique: PromptTechnique = PromptTechnique.auto


class CompareRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    persona: Persona = Persona.architect
    style: PromptStyle = PromptStyle.technical
    techniques: list[PromptTechnique] = Field(
        default_factory=lambda: [
            PromptTechnique.zero_shot,
            PromptTechnique.role,
            PromptTechnique.few_shot,
            PromptTechnique.chain_of_thought,
            PromptTechnique.step_back,
            PromptTechnique.critique_refine,
            PromptTechnique.style_variation,
        ],
        min_length=2,
    )


class TraceStep(BaseModel):
    node: str
    detail: str


class AskResponse(BaseModel):
    technique: PromptTechnique
    answer: str
    prompt_preview: str
    trace: list[TraceStep]
    metadata: dict[str, str] = Field(default_factory=dict)


class CompareResponse(BaseModel):
    question: str
    persona: Persona
    style: PromptStyle
    responses: list[AskResponse]


class GraphNode(BaseModel):
    id: str
    label: str
    x: int
    y: int


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphResponse(BaseModel):
    title: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
