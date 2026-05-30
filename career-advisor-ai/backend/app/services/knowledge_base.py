from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9+#./-]*")


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    title: str
    category: str
    content: str
    url: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredKnowledgeItem:
    item: KnowledgeItem
    score: float


class MiniVectorStore:
    def __init__(self, items: list[KnowledgeItem]) -> None:
        self.items = items
        self._idf = self._build_idf(items)
        self._vectors = [self._embed(item.content) for item in items]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return TOKEN_PATTERN.findall(text.lower())

    def _build_idf(self, items: list[KnowledgeItem]) -> dict[str, float]:
        docs = [set(self._tokenize(item.content)) for item in items]
        df = Counter(token for doc in docs for token in doc)
        corpus_size = max(len(items), 1)
        return {
            token: math.log((1 + corpus_size) / (1 + freq)) + 1
            for token, freq in df.items()
        }

    def _embed(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        tf = Counter(tokens)
        vector: dict[str, float] = {}
        norm = 0.0
        for token, freq in tf.items():
            weight = float(freq) * self._idf.get(token, 1.0)
            vector[token] = weight
            norm += weight * weight

        if norm == 0.0:
            return {}

        norm = math.sqrt(norm)
        return {token: value / norm for token, value in vector.items()}

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(token, 0.0) for token, value in left.items())

    def search(
        self,
        query: str,
        *,
        limit: int = 6,
        categories: set[str] | None = None,
    ) -> list[ScoredKnowledgeItem]:
        qvec = self._embed(query)
        scored: list[ScoredKnowledgeItem] = []

        for item, item_vec in zip(self.items, self._vectors, strict=True):
            if categories and item.category not in categories:
                continue
            score = self._cosine(qvec, item_vec)
            if score > 0.0:
                scored.append(ScoredKnowledgeItem(item=item, score=score))

        scored.sort(key=lambda entry: entry.score, reverse=True)
        return scored[:limit]


class CareerKnowledgeBase:
    def __init__(self) -> None:
        self.items = self._seed_items()
        self.vector_store = MiniVectorStore(self.items)

    def retrieve(self, query: str, *, limit: int = 6) -> list[ScoredKnowledgeItem]:
        return self.vector_store.search(query, limit=limit)

    def job_posts(self) -> list[KnowledgeItem]:
        return [item for item in self.items if item.category == "job"]

    def resources_for_skill(self, skill: str, *, limit: int = 2) -> list[KnowledgeItem]:
        results = self.vector_store.search(
            f"{skill} certification course practice project",
            limit=limit,
            categories={"course", "certification", "resource"},
        )
        return [entry.item for entry in results]

    @staticmethod
    def _seed_items() -> list[KnowledgeItem]:
        return [
            KnowledgeItem(
                id="job-ml-eng-01",
                title="Machine Learning Engineer",
                category="job",
                content=(
                    "Role: Machine Learning Engineer at NovaAI, Bengaluru hybrid. "
                    "Requires python, machine learning, feature engineering, mlops, docker, sql, aws. "
                    "Preferred: fastapi, langchain, model evaluation, responsible ai practices."
                ),
                url="https://careers.example.com/jobs/ml-engineer",
                metadata={
                    "company": "NovaAI",
                    "location": "Bengaluru",
                    "required_skills": [
                        "python",
                        "machine learning",
                        "feature engineering",
                        "mlops",
                        "docker",
                        "sql",
                        "aws",
                    ],
                },
            ),
            KnowledgeItem(
                id="job-data-scientist-01",
                title="Data Scientist - Product Analytics",
                category="job",
                content=(
                    "Role: Data Scientist at Orbit Commerce, remote India. "
                    "Requires python, statistics, experimentation, sql, dashboarding, communication. "
                    "Preferred: causal inference, recommendation systems, stakeholder management."
                ),
                url="https://careers.example.com/jobs/data-scientist",
                metadata={
                    "company": "Orbit Commerce",
                    "location": "Remote",
                    "required_skills": [
                        "python",
                        "statistics",
                        "experimentation",
                        "sql",
                        "dashboarding",
                        "communication",
                    ],
                },
            ),
            KnowledgeItem(
                id="job-ai-pm-01",
                title="AI Product Manager",
                category="job",
                content=(
                    "Role: AI Product Manager at BrightPath, Mumbai onsite. "
                    "Requires product strategy, roadmap planning, analytics, user research, ai fundamentals, prompt design. "
                    "Preferred: experimentation, leadership, stakeholder communication."
                ),
                url="https://careers.example.com/jobs/ai-product-manager",
                metadata={
                    "company": "BrightPath",
                    "location": "Mumbai",
                    "required_skills": [
                        "product strategy",
                        "roadmap planning",
                        "analytics",
                        "user research",
                        "ai fundamentals",
                        "prompt design",
                    ],
                },
            ),
            KnowledgeItem(
                id="job-genai-dev-01",
                title="Generative AI Developer",
                category="job",
                content=(
                    "Role: Generative AI Developer at SkillForge, Hyderabad hybrid. "
                    "Requires python, fastapi, langchain, langgraph, vector databases, prompt engineering, evaluation. "
                    "Preferred: react, cloud deployment, model monitoring."
                ),
                url="https://careers.example.com/jobs/genai-developer",
                metadata={
                    "company": "SkillForge",
                    "location": "Hyderabad",
                    "required_skills": [
                        "python",
                        "fastapi",
                        "langchain",
                        "langgraph",
                        "vector databases",
                        "prompt engineering",
                        "evaluation",
                    ],
                },
            ),
            KnowledgeItem(
                id="job-cloud-data-01",
                title="Cloud Data Engineer",
                category="job",
                content=(
                    "Role: Cloud Data Engineer at FinStack, Pune hybrid. "
                    "Requires sql, spark, airflow, python, data modeling, aws, data quality. "
                    "Preferred: dbt, lakehouse architecture, observability."
                ),
                url="https://careers.example.com/jobs/cloud-data-engineer",
                metadata={
                    "company": "FinStack",
                    "location": "Pune",
                    "required_skills": [
                        "sql",
                        "spark",
                        "airflow",
                        "python",
                        "data modeling",
                        "aws",
                        "data quality",
                    ],
                },
            ),
            KnowledgeItem(
                id="cert-cloud-01",
                title="AWS Certified Machine Learning Engineer",
                category="certification",
                content=(
                    "Certification covering model development, deployment, MLOps, and monitoring on AWS. "
                    "Best for professionals targeting machine learning engineering and cloud AI roles."
                ),
                url="https://aws.amazon.com/certification/",
            ),
            KnowledgeItem(
                id="cert-pm-01",
                title="AI Product Management Specialization",
                category="certification",
                content=(
                    "Certification on AI product strategy, experimentation, user-centric discovery, and roadmap tradeoffs. "
                    "Good for product managers moving into AI-first products."
                ),
                url="https://www.coursera.org/",
            ),
            KnowledgeItem(
                id="cert-data-01",
                title="Google Data Analytics Professional Certificate",
                category="certification",
                content=(
                    "Hands-on analytics credential focused on SQL, spreadsheets, dashboarding, and business storytelling."
                ),
                url="https://grow.google/certificates/data-analytics/",
            ),
            KnowledgeItem(
                id="course-hf-llm",
                title="Hugging Face LLM Course",
                category="course",
                content=(
                    "Learn large language models with practical transformers workflows, fine-tuning, evaluation, and applications."
                ),
                url="https://huggingface.co/learn/llm-course",
            ),
            KnowledgeItem(
                id="course-hf-agents",
                title="Hugging Face Agents Course",
                category="course",
                content=(
                    "Build and deploy AI agents, tool use, orchestration patterns, and practical agentic workflows."
                ),
                url="https://huggingface.co/learn/agents-course",
            ),
            KnowledgeItem(
                id="course-pair-guidebook",
                title="People + AI Guidebook",
                category="resource",
                content=(
                    "Human-centered AI design guidance, fairness checklists, user trust patterns, and responsible UX principles."
                ),
                url="https://pair.withgoogle.com/guidebook/",
            ),
            KnowledgeItem(
                id="resource-google-responsible-ai",
                title="Google Responsible Generative AI Toolkit",
                category="resource",
                content=(
                    "Operational practices for governance, safety testing, risk assessment, and post-launch monitoring."
                ),
                url="https://ai.google.dev/responsible/",
            ),
            KnowledgeItem(
                id="resource-anthropic-constitution",
                title="Anthropic Constitutional AI",
                category="resource",
                content=(
                    "Safety strategy that emphasizes transparent process-based training, oversight, and red-team driven iteration."
                ),
                url="https://www.anthropic.com/constitution",
            ),
            KnowledgeItem(
                id="resource-resume-01",
                title="High-Impact Resume Checklist",
                category="resource",
                content=(
                    "Resume best practices: quantified outcomes, domain keywords, problem-action-result bullets, and ATS readability."
                ),
                url="https://www.indeed.com/career-advice/resumes-cover-letters",
            ),
            KnowledgeItem(
                id="resource-interview-01",
                title="Structured Interview Preparation",
                category="resource",
                content=(
                    "Preparation framework covering STAR stories, role-specific case rounds, and technical depth rehearsal."
                ),
                url="https://www.themuse.com/advice/interview-preparation",
            ),
        ]
