from __future__ import annotations

import hashlib
import json
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
        self.skill_vocabulary = self._build_skill_vocabulary()
        self.session_memory: dict[str, list[str]] = {}
        self.graph = self._build_graph()

    def _build_skill_vocabulary(self) -> set[str]:
        skills: set[str] = set()
        for blueprint in ROLE_BLUEPRINTS:
            skills.update(item.strip().lower() for item in blueprint.get("skills", []))

        for job in self.knowledge_base.job_posts():
            skills.update(item.strip().lower() for item in job.metadata.get("required_skills", []))

        return {item for item in skills if item}

    def _extract_resume_skills(self, resume_text: str) -> list[str]:
        if not resume_text.strip():
            return []

        resume_l = resume_text.lower()
        extracted = [skill for skill in self.skill_vocabulary if skill in resume_l]
        return _normalize_terms(extracted)

    def _role_evidence_score(self, role_name: str, role_skills: set[str], state: WorkflowState) -> float:
        contexts = state.get("retrieved_context", [])
        if not contexts:
            return 0.0

        role_l = role_name.lower()
        role_tokens = {token for token in re.findall(r"[a-z0-9]+", role_l) if len(token) > 2}

        role_hits = 0
        skill_hits = 0

        for item in contexts:
            text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
            if role_l in text or any(token in text for token in role_tokens):
                role_hits += 1
            if any(skill in text for skill in role_skills):
                skill_hits += 1

        score = (0.65 * (role_hits / max(len(contexts), 1))) + (0.35 * (skill_hits / max(len(contexts), 1)))
        return round(min(1.0, score), 3)

    def _build_market_outlook(
        self,
        role_name: str,
        evidence_score: float,
        skill_fit: float,
        missing_skills: list[str],
        preferred_locations: list[str],
    ) -> str:
        if evidence_score >= 0.66:
            demand = "Current retrieval shows strong role demand signals"
        elif evidence_score >= 0.35:
            demand = "Current retrieval shows moderate role demand signals"
        else:
            demand = "Current retrieval has limited direct demand signals"

        fit_line = f"profile fit is {round(skill_fit * 100)}% based on skill overlap"
        location_line = f" in {preferred_locations[0]}" if preferred_locations else ""
        gap_line = (
            f". Priority upskill areas: {', '.join(missing_skills[:2])}."
            if missing_skills
            else "."
        )
        return f"{demand} for {role_name}{location_line}; {fit_line}{gap_line}"

    def _infer_location_from_text(self, text: str, preferred_locations: list[str]) -> str:
        text_l = text.lower()
        for location in preferred_locations:
            if location.lower() in text_l:
                return location

        known = [
            "remote",
            "hybrid",
            "onsite",
            "bengaluru",
            "bangalore",
            "hyderabad",
            "pune",
            "mumbai",
            "chennai",
            "delhi",
            "india",
        ]
        for token in known:
            if token in text_l:
                return token.title()
        return "Not specified"

    def _fetch_live_job_matches(self, state: WorkflowState) -> list[dict[str, Any]]:
        if not self.settings.tavily_api_key:
            return []

        try:
            from tavily import TavilyClient  # type: ignore
        except Exception:
            return []

        profile = state.get("profile", {})
        skills = set(state.get("normalized_skills", []))
        targets = state.get("normalized_targets", [])
        preferred_locations = [str(loc).strip() for loc in profile.get("preferred_locations", []) if str(loc).strip()]

        role_hint = ", ".join(targets[:2]) or str(profile.get("current_role", "AI engineer"))
        location_hint = ", ".join(preferred_locations[:2]) or "India"
        query = (
            f"Latest hiring openings for {role_hint} roles in {location_hint}. "
            "Include role title, company, key skills, and location."
        )

        try:
            result = TavilyClient(api_key=self.settings.tavily_api_key).search(
                query=query,
                max_results=10,
                topic="general",
            )
        except Exception:
            return []

        rows = result.get("results", []) if isinstance(result, dict) else []
        if not rows:
            return []

        matches: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        target_tokens = {
            token
            for target in targets
            for token in re.findall(r"[a-z0-9]+", target)
            if len(token) > 2
        }

        for row in rows:
            title_raw = str(row.get("title", "")).strip()
            url = str(row.get("url", "")).strip()
            snippet = str(row.get("content", "")).strip()
            if not title_raw:
                continue
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            text_blob = f"{title_raw} {snippet}".lower()
            title = re.split(r"\s[|\-]\s", title_raw, maxsplit=1)[0].strip() or title_raw

            company = "Web Listing"
            parts = re.split(r"\bat\b", title_raw, flags=re.IGNORECASE)
            if len(parts) > 1:
                candidate = re.split(r"[|\-]", parts[1], maxsplit=1)[0].strip()
                if candidate:
                    company = candidate

            required_skills = {skill for skill in self.skill_vocabulary if skill in text_blob}
            overlap = sorted(skills & required_skills)
            missing = sorted(required_skills - skills)

            role_phrase_bonus = 0.1 if any(target in text_blob for target in targets) else 0.0
            role_token_overlap = len(target_tokens & set(re.findall(r"[a-z0-9]+", text_blob))) / max(
                len(target_tokens),
                1,
            )
            role_relevance = max(role_phrase_bonus, min(0.25, role_token_overlap * 0.35))

            skill_score = len(overlap) / max(len(required_skills), 3)
            market_signal_bonus = 0.05 if any(token in text_blob for token in ["hiring", "job", "career", "opening"]) else 0.0

            # Keep live candidates even when snippets are sparse on explicit skills.
            match_score = min(0.96, 0.2 + (0.55 * skill_score) + role_relevance + market_signal_bonus)
            if match_score < 0.18:
                continue

            stable_id_source = url or title_raw
            job_id = f"live-{hashlib.sha1(stable_id_source.encode('utf-8')).hexdigest()[:10]}"

            matches.append(
                {
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location": self._infer_location_from_text(text_blob, preferred_locations),
                    "match_score": round(match_score, 2),
                    "rationale": [
                        f"Live web listing evidence from Tavily query for '{role_hint}'.",
                        f"Matched skills: {', '.join(overlap[:5]) or 'Limited direct overlap in snippet'}.",
                    ],
                    "missing_skills": missing[:5],
                    "job_url": url or None,
                    "source": "tavily-live",
                }
            )

        matches.sort(key=lambda item: item["match_score"], reverse=True)
        return matches[:5]

    def _llm_profile_summary(
        self,
        profile: dict[str, Any],
        normalized_skills: list[str],
        normalized_interests: list[str],
        resume_text: str,
    ) -> str | None:
        if not self.model:
            return None

        resume_excerpt = resume_text[:1200] if resume_text else "No resume text provided."
        user_prompt = (
            "Create a concise profile summary for career advisory use.\n"
            "Constraints:\n"
            "- 2 to 3 sentences\n"
            "- Mention strengths, focus areas, and likely trajectory\n"
            "- Do not mention protected traits\n"
            "- Ground summary in profile and resume evidence only\n\n"
            f"Profile data: {profile}\n"
            f"Normalized skills: {normalized_skills}\n"
            f"Normalized interests: {normalized_interests}\n"
            f"Resume excerpt: {resume_excerpt}"
        )

        response = self.model.invoke(
            [
                SystemMessage(content="You are a careful career analysis assistant."),
                HumanMessage(content=user_prompt),
            ]
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        cleaned = text.strip()
        return cleaned or None

    def _llm_resume_analysis(
        self,
        profile: dict[str, Any],
        resume_text: str,
        recommendations: list[dict[str, Any]],
        skill_gaps: list[dict[str, Any]],
        retrieved_context: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not self.model:
            return None

        prompt = (
            "Analyze the resume for career readiness and return STRICT JSON only.\n"
            "JSON schema:\n"
            "{\n"
            '  "overall_score": float between 0 and 1,\n'
            '  "strengths": [string],\n'
            '  "issues": [{"issue": string, "severity": "low|medium|high", "suggestion": string}],\n'
            '  "rewritten_summary": string\n'
            "}\n"
            "Rules:\n"
            "- Use evidence from resume text and role recommendations\n"
            "- Keep strengths and issues practical and specific\n"
            "- 3-6 strengths, 3-8 issues\n"
            "- Do not wrap output in markdown fences\n\n"
            f"Profile: {profile}\n"
            f"Top recommendations: {recommendations[:3]}\n"
            f"Top skill gaps: {skill_gaps[:6]}\n"
            f"Retrieved context: {retrieved_context[:4]}\n"
            f"Resume text:\n{resume_text[:5000]}"
        )

        response = self.model.invoke(
            [
                SystemMessage(content="You are a strict JSON resume evaluator."),
                HumanMessage(content=prompt),
            ]
        )
        raw = response.content if isinstance(response.content, str) else str(response.content)
        cleaned = raw.strip().strip("`")

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

        if not isinstance(parsed, dict):
            return None

        overall_score = parsed.get("overall_score")
        strengths = parsed.get("strengths", [])
        issues = parsed.get("issues", [])
        rewritten_summary = parsed.get("rewritten_summary", "")

        try:
            overall_score = float(overall_score)
        except (TypeError, ValueError):
            return None

        if not isinstance(strengths, list) or not isinstance(issues, list) or not isinstance(rewritten_summary, str):
            return None

        normalized_issues: list[dict[str, str]] = []
        for item in issues:
            if not isinstance(item, dict):
                continue
            issue = str(item.get("issue", "")).strip()
            severity = str(item.get("severity", "medium")).strip().lower()
            suggestion = str(item.get("suggestion", "")).strip()
            if not issue or not suggestion:
                continue
            if severity not in {"low", "medium", "high"}:
                severity = "medium"
            normalized_issues.append({"issue": issue, "severity": severity, "suggestion": suggestion})

        normalized_strengths = [str(item).strip() for item in strengths if str(item).strip()]
        rewritten_summary = rewritten_summary.strip()
        if not normalized_strengths or not normalized_issues or not rewritten_summary:
            return None

        return {
            "overall_score": max(0.0, min(1.0, round(overall_score, 2))),
            "strengths": normalized_strengths[:8],
            "issues": normalized_issues[:10],
            "rewritten_summary": rewritten_summary,
        }

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
        resume_skills = self._extract_resume_skills(state.get("resume_text", ""))
        normalized_skills = _normalize_terms([*profile.get("skills", []), *resume_skills])
        normalized_interests = _normalize_terms(profile.get("interests", []))
        normalized_targets = _normalize_terms(profile.get("target_roles", []))

        fallback_summary = (
            f"{profile.get('current_role', 'Professional')} profile with "
            f"{profile.get('years_experience', 0)} years experience. "
            f"Top skills: {', '.join(profile.get('skills', [])[:6]) or 'Not provided'}. "
            f"Career interests: {', '.join(profile.get('interests', [])[:4]) or 'Not provided'}."
        )
        summary = self._llm_profile_summary(
            profile,
            normalized_skills,
            normalized_interests,
            state.get("resume_text", ""),
        ) or fallback_summary

        return {
            "normalized_skills": normalized_skills,
            "normalized_interests": normalized_interests,
            "normalized_targets": normalized_targets,
            "profile_summary": summary,
            "trace": _append_trace(
                state,
                "profile_analysis_agent",
                (
                    f"Analyzed profile with {len(normalized_skills)} normalized skills "
                    f"({len(resume_skills)} extracted from resume) and {len(normalized_interests)} interests"
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
        preferred_locations = [
            str(loc).strip() for loc in state.get("profile", {}).get("preferred_locations", []) if str(loc).strip()
        ]
        years = float(state["profile"].get("years_experience", 0.0))

        ranked: list[tuple[float, dict[str, Any], list[str], list[str]]] = []
        for blueprint in ROLE_BLUEPRINTS:
            role_skills = {item.lower() for item in blueprint["skills"]}
            role_interests = {item.lower() for item in blueprint["interests"]}
            matching = sorted(skills & role_skills)
            missing = sorted(role_skills - skills)

            skill_fit = len(matching) / max(len(role_skills), 1)
            interest_fit = len(interests & role_interests) / max(len(role_interests), 1)
            evidence_fit = self._role_evidence_score(blueprint["role"], role_skills, state)

            min_exp, max_exp = blueprint["experience"]
            if years < min_exp:
                exp_fit = max(0.25, 1 - ((min_exp - years) / max(min_exp, 1)))
            elif years > max_exp:
                exp_fit = max(0.45, 1 - ((years - max_exp) / max(max_exp, 1)))
            else:
                exp_fit = 1.0

            exact_target_bonus = 0.12 if blueprint["role"].lower() in targets else 0.0
            partial_target_bonus = 0.05 if any(target in blueprint["role"].lower() for target in targets) else 0.0
            target_bonus = max(exact_target_bonus, partial_target_bonus)
            confidence = min(
                0.98,
                (0.45 * skill_fit)
                + (0.2 * interest_fit)
                + (0.15 * exp_fit)
                + (0.2 * evidence_fit)
                + target_bonus,
            )
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
                    "market_outlook": self._build_market_outlook(
                        blueprint["role"],
                        evidence_score=self._role_evidence_score(blueprint["role"], role_skills, state),
                        skill_fit=skill_fit,
                        missing_skills=missing,
                        preferred_locations=preferred_locations,
                    ),
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
            "metadata": {
                **state.get("metadata", {}),
                "recommendation_mode": "evidence-weighted",
            },
            "trace": _append_trace(
                state,
                "career_recommendation_agent",
                f"Generated {len(recommendations)} recommendations and {len(skill_gaps)} skill gaps",
            ),
        }

    def _job_matching_agent(self, state: WorkflowState) -> WorkflowState:
        live_matches = self._fetch_live_job_matches(state)
        if live_matches:
            return {
                "job_matches": live_matches,
                "metadata": {
                    **state.get("metadata", {}),
                    "job_data_source": "tavily-live",
                },
                "trace": _append_trace(
                    state,
                    "job_matching_agent",
                    f"Matched {len(live_matches)} jobs using live Tavily web results",
                ),
            }

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
                        "Curated sample listing from local knowledge base.",
                        f"Matched skills: {', '.join(overlap[:5]) or 'No direct overlap'}.",
                        f"Role requires {len(required)} core skill(s).",
                    ],
                    "missing_skills": missing[:5],
                    "job_url": job.url,
                    "source": "local-kb",
                }
            )

        matches.sort(key=lambda item: item["match_score"], reverse=True)

        return {
            "job_matches": matches[:5],
            "metadata": {
                **state.get("metadata", {}),
                "job_data_source": "local-kb",
            },
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

        llm_analysis = self._llm_resume_analysis(
            profile=profile,
            resume_text=resume,
            recommendations=state.get("career_recommendations", []),
            skill_gaps=state.get("skill_gaps", []),
            retrieved_context=state.get("retrieved_context", []),
        )
        if llm_analysis is not None:
            return {
                "resume_analysis": llm_analysis,
                "trace": _append_trace(
                    state,
                    "resume_analysis_agent",
                    "Generated model-based resume analysis grounded in resume and role context",
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

        base_metadata = {
            "provider": self.settings.normalized_provider,
            "model": self.settings.selected_model_name if self.model else "mock-llm",
            "rag_docs": str(len(state.get("retrieved_context", []))),
            "safety_mode": "enabled",
            "deep_agent_support": "enabled" if self.settings.deep_agent_enabled else "disabled",
        }
        metadata = {**base_metadata, **state.get("metadata", {})}

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
