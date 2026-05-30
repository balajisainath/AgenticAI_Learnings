from pydantic import BaseModel, Field, field_validator


class CareerProfile(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    current_role: str = Field(..., min_length=2, max_length=120)
    years_experience: float = Field(..., ge=0.0, le=45.0)
    education: str = Field(default="bachelors", max_length=80)
    skills: list[str] = Field(default_factory=list, min_length=1, max_length=30)
    interests: list[str] = Field(default_factory=list, max_length=20)
    target_roles: list[str] = Field(default_factory=list, max_length=10)
    preferred_locations: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("skills", "interests", "target_roles", "preferred_locations")
    @classmethod
    def normalize_lists(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in values:
            value = raw.strip()
            if not value:
                continue
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(value)
        return normalized


class CareerAnalysisRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=80)
    profile: CareerProfile
    resume_text: str | None = Field(default=None, max_length=12000)
    priorities: list[str] = Field(
        default_factory=lambda: [
            "career_growth",
            "job_match_quality",
            "skill_development",
            "interview_readiness",
        ],
        max_length=8,
    )


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=2, max_length=80)
    message: str = Field(..., min_length=2, max_length=4000)
    profile: CareerProfile | None = None


class TraceStep(BaseModel):
    node: str
    detail: str


class RetrievedItem(BaseModel):
    id: str
    title: str
    category: str
    url: str
    score: float
    snippet: str


class CareerRecommendation(BaseModel):
    role: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    rationale: list[str] = Field(default_factory=list)
    market_outlook: str
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class JobMatch(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    rationale: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class SkillGap(BaseModel):
    skill: str
    priority: str
    why_important: str
    suggested_resources: list[str] = Field(default_factory=list)


class RoadmapStep(BaseModel):
    phase: str
    duration_weeks: int = Field(..., ge=1, le=26)
    goals: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)


class ResumeIssue(BaseModel):
    issue: str
    severity: str
    suggestion: str


class ResumeAnalysis(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0)
    strengths: list[str] = Field(default_factory=list)
    issues: list[ResumeIssue] = Field(default_factory=list)
    rewritten_summary: str


class SafetyReport(BaseModel):
    overall_risk: str
    flags: list[str] = Field(default_factory=list)
    bias_checks: list[str] = Field(default_factory=list)
    transparency_notes: list[str] = Field(default_factory=list)


class CareerAnalysisResponse(BaseModel):
    session_id: str
    profile_summary: str
    career_recommendations: list[CareerRecommendation]
    job_matches: list[JobMatch]
    skill_gaps: list[SkillGap]
    roadmap: list[RoadmapStep]
    resume_analysis: ResumeAnalysis
    safety_report: SafetyReport
    retrieved_context: list[RetrievedItem]
    memory_notes: list[str] = Field(default_factory=list)
    trace: list[TraceStep] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    safety_report: SafetyReport
    trace: list[TraceStep] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class DeepResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    session_id: str | None = Field(default=None, max_length=80)


class DeepResearchResponse(BaseModel):
    summary: str
    sources: list[str] = Field(default_factory=list)
    used_deep_agent: bool
    metadata: dict[str, str] = Field(default_factory=dict)


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
