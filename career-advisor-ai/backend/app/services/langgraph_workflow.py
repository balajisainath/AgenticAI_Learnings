from __future__ import annotations

import re
from collections import Counter
from typing import Any, TypedDict
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.core.config import Settings
from app.domain.schemas import (
    CareerAnalysisRequest,
    CareerAnalysisResponse,
    CareerRecommendation,
    ChatRequest,
    ChatResponse,
    GraphResponse,
    JobMatch,
    ResumeAnalysis,
    RetrievedItem,
    RoadmapStep,
    SafetyReport,
    SkillGap,
    TraceStep,
)
from app.prompts.few_shot import CHAT_FEW_SHOTS
from app.prompts.personas import CAREER_ADVISOR_PERSONA, INTERVIEW_COACH_PERSONA
from app.prompts.styles import EXPLAINABILITY_CHECKLIST, RESPONSIBLE_AI_GUARDRAILS
from app.services.knowledge_base import CareerKnowledgeBase, KnowledgeItem
from app.services.llm_factory import build_chat_model


class WorkflowState(TypedDict, total=False):
    session_id: str
    profile: dict[str, Any]
    resume_text: str
    priorities: list[str]
    normalized_skills: list[str]
    normalized_interests: list[str]
    normalized_targets: list[str]
    profile_summary: str
    memory_notes: list[str]
    retrieved_context: list[dict[str, Any]]
    career_recommendations: list[dict[str, Any]]
    job_matches: list[dict[str, Any]]
    skill_gaps: list[dict[str, Any]]
    roadmap: list[dict[str, Any]]
    resume_analysis: dict[str, Any]
    safety_report: dict[str, Any]
    metadata: dict[str, str]
    trace: list[dict[str, str]]


ROLE_BLUEPRINTS: list[dict[str, Any]] = [
    {
        "role": "Machine Learning Engineer",
        "skills": ["python", "machine learning", "mlops", "sql", "docker", "aws"],
        "interests": ["ai", "data", "automation", "engineering"],
        "experience": (1.0, 8.0),
        "market_outlook": "Strong demand across product and platform teams.",
    },
    {
        "role": "Generative AI Developer",
        "skills": [
            "python",
            "fastapi",
            "langchain",
            "langgraph",
            "prompt engineering",
            "vector databases",
        ],
        "interests": ["ai", "agents", "developer tools", "llm applications"],
        "experience": (0.5, 7.0),
        "market_outlook": "Fast-growing demand in startups and innovation teams.",
    },
    {
        "role": "AI Product Manager",
        "skills": [
            "product strategy",
            "roadmap planning",
            "analytics",
            "user research",
            "ai fundamentals",
            "communication",
        ],
        "interests": ["product", "business", "ai", "customer impact"],
        "experience": (2.0, 12.0),
        "market_outlook": "Growing demand for AI-native product leadership.",
    },
    {
        "role": "Data Scientist",
        "skills": ["python", "statistics", "experimentation", "sql", "dashboarding"],
        "interests": ["analytics", "data", "experiments", "insights"],
        "experience": (1.0, 10.0),
        "market_outlook": "Stable demand with high cross-domain mobility.",
    },
]


def _append_trace(state: WorkflowState, node: str, detail: str) -> list[dict[str, str]]:
    trace = list(state.get("trace", []))
    trace.append({"node": node, "detail": detail})
    return trace


def _normalize_terms(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip().lower()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


class CareerAdvisorWorkflow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = build_chat_model(settings)
        self.knowledge_base = CareerKnowledgeBase()
        self.session_memory: dict[str, list[str]] = {}
        self.graph = self._build_graph()

    def run(self, request: CareerAnalysisRequest) -> CareerAnalysisResponse:
        session_id = request.session_id or f"career-{uuid4().hex[:10]}"
        initial_state: WorkflowState = {
            "session_id": session_id,
            "profile": request.profile.model_dump(),
            "resume_text": request.resume_text or "",
            "priorities": request.priorities,
            "trace": [],
        }
        result = self.graph.invoke(initial_state)

        return CareerAnalysisResponse(
            session_id=result["session_id"],
            profile_summary=result["profile_summary"],
            career_recommendations=[CareerRecommendation(**item) for item in result["career_recommendations"]],
            job_matches=[JobMatch(**item) for item in result["job_matches"]],
            skill_gaps=[SkillGap(**item) for item in result["skill_gaps"]],
            roadmap=[RoadmapStep(**item) for item in result["roadmap"]],
            resume_analysis=ResumeAnalysis(**result["resume_analysis"]),
            safety_report=SafetyReport(**result["safety_report"]),
            retrieved_context=[RetrievedItem(**item) for item in result["retrieved_context"]],
            memory_notes=result.get("memory_notes", []),
            trace=[TraceStep(**item) for item in result.get("trace", [])],
            metadata=result.get("metadata", {}),
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        memory_notes = self.session_memory.get(request.session_id, [])
        trace = [
            {
                "node": "memory_agent",
                "detail": f"Loaded {len(memory_notes)} notes for session {request.session_id}",
            }
        ]

        if self.model:
            messages: list[Any] = [
                SystemMessage(
                    content="\n".join(
                        [
                            CAREER_ADVISOR_PERSONA,
                            INTERVIEW_COACH_PERSONA,
                            "Follow fairness and safety requirements strictly.",
                            *[f"- {rule}" for rule in RESPONSIBLE_AI_GUARDRAILS],
                        ]
                    )
                ),
            ]
            for shot in CHAT_FEW_SHOTS:
                messages.append(HumanMessage(content=shot["input"]))
                messages.append(AIMessage(content=shot["output"]))

            memory_block = "\n".join(memory_notes[-3:]) if memory_notes else "No prior session memory."
            question = (
                f"Session memory:\n{memory_block}\n\n"
                f"User question:\n{request.message}\n\n"
                "Give practical interview prep/career advice with clear steps."
            )
            messages.append(HumanMessage(content=question))
            response = self.model.invoke(messages)
            answer = response.content if isinstance(response.content, str) else str(response.content)
            trace.append({"node": "career_chat_agent", "detail": "Generated model-based advisory response"})
        else:
            memory_line = memory_notes[-1] if memory_notes else "No prior context yet."
            answer = (
                "Career Advisor response (mock mode):\n"
                f"- Context used: {memory_line}\n"
                "- Focus on one target role, 3 high-impact skills, and 2 interview stories.\n"
                "- Practice 30 minutes daily on role-specific problems and mock interviews.\n"
                "- Quantify your resume bullets with measurable impact before applying."
            )
            trace.append({"node": "career_chat_agent", "detail": "Returned deterministic mock advisory response"})

        safety_report = self._safety_report_for_text(answer)
        trace.append({"node": "safety_bias_detection_agent", "detail": "Applied safety checks on chat output"})

        return ChatResponse(
            session_id=request.session_id,
            answer=answer,
            safety_report=safety_report,
            trace=[TraceStep(**item) for item in trace],
            metadata={
                "provider": self.settings.normalized_provider,
                "model": self.settings.selected_model_name if self.model else "mock-llm",
            },
        )

    def export_graph_definition(self) -> GraphResponse:
        return GraphResponse(
            title="Career Advisor Multi-Agent LangGraph",
            nodes=[
                {"id": "memory_agent", "label": "Memory Agent", "x": 60, "y": 90},
                {"id": "profile_analysis_agent", "label": "Profile Analysis Agent", "x": 250, "y": 90},
                {"id": "rag_retriever_agent", "label": "RAG Retriever", "x": 470, "y": 90},
                {"id": "career_recommendation_agent", "label": "Career Recommendation Agent", "x": 660, "y": 90},
                {"id": "job_matching_agent", "label": "Job Matching Agent", "x": 900, "y": 90},
                {"id": "roadmap_generation_agent", "label": "Roadmap Generation Agent", "x": 1110, "y": 90},
                {"id": "resume_analysis_agent", "label": "Resume Analysis Agent", "x": 1320, "y": 90},
                {"id": "safety_bias_detection_agent", "label": "Safety/Bias Detection Agent", "x": 1530, "y": 90},
                {"id": "response_compiler", "label": "Response Compiler", "x": 1760, "y": 90},
            ],
            edges=[
                {"source": "memory_agent", "target": "profile_analysis_agent"},
                {"source": "profile_analysis_agent", "target": "rag_retriever_agent"},
                {"source": "rag_retriever_agent", "target": "career_recommendation_agent"},
                {"source": "career_recommendation_agent", "target": "job_matching_agent"},
                {"source": "job_matching_agent", "target": "roadmap_generation_agent"},
                {"source": "roadmap_generation_agent", "target": "resume_analysis_agent"},
                {"source": "resume_analysis_agent", "target": "safety_bias_detection_agent"},
                {"source": "safety_bias_detection_agent", "target": "response_compiler"},
            ],
        )

    def _memory_agent(self, state: WorkflowState) -> WorkflowState:
        notes = self.session_memory.get(state["session_id"], [])
        return {
            "memory_notes": notes,
            "trace": _append_trace(state, "memory_agent", f"Recovered {len(notes)} memory notes"),
        }

    def _profile_analysis_agent(self, state: WorkflowState) -> WorkflowState:
        profile = state["profile"]
        normalized_skills = _normalize_terms(profile.get("skills", []))
        normalized_interests = _normalize_terms(profile.get("interests", []))
        normalized_targets = _normalize_terms(profile.get("target_roles", []))

        summary = (
            f"{profile.get('current_role', 'Professional')} profile with "
            f"{profile.get('years_experience', 0)} years experience. "
            f"Top skills: {', '.join(profile.get('skills', [])[:6]) or 'Not provided'}. "
            f"Career interests: {', '.join(profile.get('interests', [])[:4]) or 'Not provided'}."
        )

        return {
            "normalized_skills": normalized_skills,
            "normalized_interests": normalized_interests,
            "normalized_targets": normalized_targets,
            "profile_summary": summary,
            "trace": _append_trace(
                state,
                "profile_analysis_agent",
                (
                    f"Analyzed profile with {len(normalized_skills)} normalized skills and "
                    f"{len(normalized_interests)} interests"
                ),
            ),
        }

    def _rag_retriever_agent(self, state: WorkflowState) -> WorkflowState:
        profile = state["profile"]
        query_parts = [
            profile.get("current_role", ""),
            *profile.get("skills", []),
            *profile.get("interests", []),
            *profile.get("target_roles", []),
            state.get("resume_text", ""),
        ]
        query = " ".join(part for part in query_parts if part).strip()

        docs = self.knowledge_base.retrieve(query, limit=self.settings.rag_top_k)
        retrieved_context = [
            {
                "id": entry.item.id,
                "title": entry.item.title,
                "category": entry.item.category,
                "url": entry.item.url,
                "score": round(entry.score, 3),
                "snippet": entry.item.content[:180],
            }
            for entry in docs
        ]

        return {
            "retrieved_context": retrieved_context,
            "trace": _append_trace(
                state,
                "rag_retriever_agent",
                f"Retrieved {len(retrieved_context)} context documents from vector index",
            ),
        }

    def _career_recommendation_agent(self, state: WorkflowState) -> WorkflowState:
        skills = set(state.get("normalized_skills", []))
        interests = set(state.get("normalized_interests", []))
        targets = set(state.get("normalized_targets", []))
        years = float(state["profile"].get("years_experience", 0.0))

        ranked: list[tuple[float, dict[str, Any], list[str], list[str]]] = []
        for blueprint in ROLE_BLUEPRINTS:
            role_skills = {item.lower() for item in blueprint["skills"]}
            role_interests = {item.lower() for item in blueprint["interests"]}
            matching = sorted(skills & role_skills)
            missing = sorted(role_skills - skills)

            skill_fit = len(matching) / max(len(role_skills), 1)
            interest_fit = len(interests & role_interests) / max(len(role_interests), 1)

            min_exp, max_exp = blueprint["experience"]
            if years < min_exp:
                exp_fit = max(0.25, 1 - ((min_exp - years) / max(min_exp, 1)))
            elif years > max_exp:
                exp_fit = max(0.45, 1 - ((years - max_exp) / max(max_exp, 1)))
            else:
                exp_fit = 1.0

            target_bonus = 0.08 if any(target in blueprint["role"].lower() for target in targets) else 0.0
            confidence = min(0.98, (0.55 * skill_fit) + (0.25 * interest_fit) + (0.2 * exp_fit) + target_bonus)
            ranked.append((confidence, blueprint, matching, missing))

        ranked.sort(key=lambda item: item[0], reverse=True)
        top = ranked[:3]

        recommendations: list[dict[str, Any]] = []
        gap_counter: Counter[str] = Counter()

        for confidence, blueprint, matching, missing in top:
            for skill in missing:
                gap_counter[skill] += 1

            rationale = [
                f"Skill overlap: {len(matching)}/{len(blueprint['skills'])}.",
                f"Interest alignment: {', '.join(sorted(set(state.get('normalized_interests', [])) & {i.lower() for i in blueprint['interests']})) or 'Limited overlap'}.",
                f"Experience fit evaluated against {blueprint['experience'][0]}-{blueprint['experience'][1]} years band.",
            ]

            recommendations.append(
                {
                    "role": blueprint["role"],
                    "confidence_score": round(confidence, 2),
                    "rationale": rationale,
                    "market_outlook": blueprint["market_outlook"],
                    "matching_skills": matching,
                    "missing_skills": missing[:5],
                }
            )

        skill_gaps: list[dict[str, Any]] = []
        for skill, count in gap_counter.most_common(8):
            priority = "high" if count >= 2 else "medium"
            resources = self.knowledge_base.resources_for_skill(skill, limit=2)
            skill_gaps.append(
                {
                    "skill": skill,
                    "priority": priority,
                    "why_important": f"This appears in {count} recommended role profile(s).",
                    "suggested_resources": [f"{item.title} ({item.url})" for item in resources],
                }
            )

        return {
            "career_recommendations": recommendations,
            "skill_gaps": skill_gaps,
            "trace": _append_trace(
                state,
                "career_recommendation_agent",
                f"Generated {len(recommendations)} recommendations and {len(skill_gaps)} skill gaps",
            ),
        }

    def _job_matching_agent(self, state: WorkflowState) -> WorkflowState:
        skills = set(state.get("normalized_skills", []))
        target_roles = set(state.get("normalized_targets", []))

        matches: list[dict[str, Any]] = []
        for job in self.knowledge_base.job_posts():
            required = {item.lower() for item in job.metadata.get("required_skills", [])}
            overlap = sorted(skills & required)
            missing = sorted(required - skills)

            skill_score = len(overlap) / max(len(required), 1)
            target_bonus = 0.1 if any(target in job.title.lower() for target in target_roles) else 0.0
            match_score = min(0.97, (0.85 * skill_score) + target_bonus)
            if match_score < 0.28:
                continue

            matches.append(
                {
                    "job_id": job.id,
                    "title": job.title,
                    "company": str(job.metadata.get("company", "Unknown")),
                    "location": str(job.metadata.get("location", "Not specified")),
                    "match_score": round(match_score, 2),
                    "rationale": [
                        f"Matched skills: {', '.join(overlap[:5]) or 'No direct overlap'}.",
                        f"Role requires {len(required)} core skill(s).",
                    ],
                    "missing_skills": missing[:5],
                }
            )

        matches.sort(key=lambda item: item["match_score"], reverse=True)

        return {
            "job_matches": matches[:5],
            "trace": _append_trace(
                state,
                "job_matching_agent",
                f"Matched {len(matches[:5])} jobs using profile-to-job skill similarity",
            ),
        }

    def _roadmap_generation_agent(self, state: WorkflowState) -> WorkflowState:
        gaps = state.get("skill_gaps", [])[:6]
        if not gaps:
            roadmap = [
                {
                    "phase": "Phase 1 - Consolidate",
                    "duration_weeks": 4,
                    "goals": ["Strengthen current strengths and portfolio storytelling"],
                    "actions": [
                        "Document 2 project case studies with measurable outcomes",
                        "Practice mock interviews twice per week",
                    ],
                    "resources": ["Hugging Face Learn (https://huggingface.co/learn)"],
                }
            ]
        else:
            buckets = [gaps[0:2], gaps[2:4], gaps[4:6]]
            labels = ["Phase 1 - Foundation", "Phase 2 - Build", "Phase 3 - Interview + Apply"]
            roadmap = []
            for label, bucket in zip(labels, buckets, strict=True):
                if not bucket:
                    continue
                skill_names = [item["skill"] for item in bucket]
                resources = [res for item in bucket for res in item.get("suggested_resources", [])][:4]
                roadmap.append(
                    {
                        "phase": label,
                        "duration_weeks": 4,
                        "goals": [f"Improve: {', '.join(skill_names)}"],
                        "actions": [
                            f"Complete one mini-project focused on {skill_names[0]}",
                            "Publish one portfolio update and seek feedback",
                            "Run weekly interview drills aligned to target roles",
                        ],
                        "resources": resources,
                    }
                )

        return {
            "roadmap": roadmap,
            "trace": _append_trace(
                state,
                "roadmap_generation_agent",
                f"Generated {len(roadmap)} roadmap phase(s)",
            ),
        }

    def _resume_analysis_agent(self, state: WorkflowState) -> WorkflowState:
        resume = state.get("resume_text", "").strip()
        profile = state["profile"]

        if not resume:
            analysis = {
                "overall_score": 0.55,
                "strengths": ["Profile details available for baseline advice."],
                "issues": [
                    {
                        "issue": "Resume text not provided.",
                        "severity": "high",
                        "suggestion": "Paste your resume to get targeted bullet-level feedback.",
                    }
                ],
                "rewritten_summary": (
                    f"{profile.get('current_role', 'Professional')} with {profile.get('years_experience', 0)} years of experience "
                    "seeking growth in AI and data-driven roles."
                ),
            }
            return {
                "resume_analysis": analysis,
                "trace": _append_trace(
                    state,
                    "resume_analysis_agent",
                    "Skipped deep resume analysis because resume text was empty",
                ),
            }

        resume_lower = resume.lower()
        strengths: list[str] = []
        issues: list[dict[str, str]] = []

        if any(token in resume_lower for token in ["led", "built", "improved", "designed"]):
            strengths.append("Action-oriented language is present.")
        if re.search(r"\d", resume):
            strengths.append("Contains measurable numbers and quantifiable detail.")
        else:
            issues.append(
                {
                    "issue": "No measurable outcomes found.",
                    "severity": "high",
                    "suggestion": "Add metrics like revenue impact, latency reduction, or conversion lift.",
                }
            )

        if len(resume) < 350:
            issues.append(
                {
                    "issue": "Resume appears too short for strong role matching.",
                    "severity": "medium",
                    "suggestion": "Expand with role-specific projects, outcomes, and tools used.",
                }
            )

        rec_skills = set()
        for rec in state.get("career_recommendations", [])[:2]:
            rec_skills.update({skill.lower() for skill in rec.get("matching_skills", [])})
            rec_skills.update({skill.lower() for skill in rec.get("missing_skills", [])})

        for skill in sorted(rec_skills)[:4]:
            if skill and skill not in resume_lower:
                issues.append(
                    {
                        "issue": f"Keyword gap for '{skill}'.",
                        "severity": "medium",
                        "suggestion": f"Add evidence of {skill} in projects or experience bullets.",
                    }
                )

        score = max(0.4, 0.9 - (0.09 * len(issues)))
        summary = (
            f"{profile.get('current_role', 'Professional')} with {profile.get('years_experience', 0)}+ years experience in "
            f"{', '.join(profile.get('skills', [])[:5])}. Focused on building impact in AI-enabled products and data-driven delivery."
        )

        analysis = {
            "overall_score": round(score, 2),
            "strengths": strengths or ["Resume contains role-relevant terminology."],
            "issues": issues,
            "rewritten_summary": summary,
        }

        return {
            "resume_analysis": analysis,
            "trace": _append_trace(
                state,
                "resume_analysis_agent",
                f"Identified {len(issues)} resume issue(s) with score {round(score, 2)}",
            ),
        }

    def _safety_bias_detection_agent(self, state: WorkflowState) -> WorkflowState:
        profile_text = " ".join(
            [
                state.get("profile_summary", ""),
                state.get("resume_text", ""),
            ]
        ).lower()

        flags: list[str] = []
        sensitive_terms = {"male", "female", "race", "religion", "pregnant", "married", "young", "old"}
        if any(term in profile_text for term in sensitive_terms):
            flags.append("Sensitive personal terms detected; they are ignored in scoring logic.")

        if any(rec.get("confidence_score", 0.0) > 0.92 for rec in state.get("career_recommendations", [])):
            flags.append("High confidence recommendation present; verify with human review.")

        if len(state.get("retrieved_context", [])) < 2:
            flags.append("Low retrieval evidence: recommendations may be less grounded.")

        risk = "low"
        if len(flags) >= 3:
            risk = "high"
        elif len(flags) >= 1:
            risk = "medium"

        safety_report = {
            "overall_risk": risk,
            "flags": flags,
            "bias_checks": [
                "Protected attributes are excluded from recommendation and job-match scoring.",
                "Recommendations are weighted by skill evidence and profile signals only.",
                "Safety design inspired by fairness and oversight principles from Microsoft/Google/Anthropic guidance.",
            ],
            "transparency_notes": EXPLAINABILITY_CHECKLIST
            + [
                "This output is advisory and should not replace human career mentoring.",
                "Confidence scores indicate relative fit, not guaranteed hiring outcomes.",
            ],
        }

        return {
            "safety_report": safety_report,
            "trace": _append_trace(
                state,
                "safety_bias_detection_agent",
                f"Completed safety pass with risk level '{risk}'",
            ),
        }

    def _response_compiler(self, state: WorkflowState) -> WorkflowState:
        notes = list(state.get("memory_notes", []))
        top_role = state.get("career_recommendations", [{}])[0].get("role", "N/A")
        top_gap = state.get("skill_gaps", [{}])[0].get("skill", "N/A")
        notes.append(f"Top role: {top_role}; Priority skill gap: {top_gap}")
        notes = notes[-6:]

        self.session_memory[state["session_id"]] = notes

        metadata = {
            "provider": self.settings.normalized_provider,
            "model": self.settings.selected_model_name if self.model else "mock-llm",
            "rag_docs": str(len(state.get("retrieved_context", []))),
            "safety_mode": "enabled",
            "deep_agent_support": "enabled" if self.settings.deep_agent_enabled else "disabled",
        }

        return {
            "memory_notes": notes,
            "metadata": metadata,
            "trace": _append_trace(state, "response_compiler", "Compiled response payload and updated memory"),
        }

    def _safety_report_for_text(self, text: str) -> SafetyReport:
        text_l = text.lower()
        flags: list[str] = []
        if any(term in text_l for term in ["male", "female", "race", "religion", "young", "old"]):
            flags.append("Potential sensitive attribute mention detected in output.")

        risk = "low" if not flags else "medium"
        return SafetyReport(
            overall_risk=risk,
            flags=flags,
            bias_checks=[
                "Advice should remain skill- and evidence-focused.",
                "Use human review for high-stakes decisions.",
            ],
            transparency_notes=[
                "Chat guidance is informational and not a hiring guarantee.",
                "Validate recommendations with mentors and real market signals.",
            ],
        )

    def _build_graph(self) -> Any:
        graph = StateGraph(WorkflowState)

        graph.add_node("memory_agent", self._memory_agent)
        graph.add_node("profile_analysis_agent", self._profile_analysis_agent)
        graph.add_node("rag_retriever_agent", self._rag_retriever_agent)
        graph.add_node("career_recommendation_agent", self._career_recommendation_agent)
        graph.add_node("job_matching_agent", self._job_matching_agent)
        graph.add_node("roadmap_generation_agent", self._roadmap_generation_agent)
        graph.add_node("resume_analysis_agent", self._resume_analysis_agent)
        graph.add_node("safety_bias_detection_agent", self._safety_bias_detection_agent)
        graph.add_node("response_compiler", self._response_compiler)

        graph.set_entry_point("memory_agent")
        graph.add_edge("memory_agent", "profile_analysis_agent")
        graph.add_edge("profile_analysis_agent", "rag_retriever_agent")
        graph.add_edge("rag_retriever_agent", "career_recommendation_agent")
        graph.add_edge("career_recommendation_agent", "job_matching_agent")
        graph.add_edge("job_matching_agent", "roadmap_generation_agent")
        graph.add_edge("roadmap_generation_agent", "resume_analysis_agent")
        graph.add_edge("resume_analysis_agent", "safety_bias_detection_agent")
        graph.add_edge("safety_bias_detection_agent", "response_compiler")
        graph.add_edge("response_compiler", END)

        return graph.compile()
