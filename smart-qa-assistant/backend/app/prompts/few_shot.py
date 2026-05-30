from app.domain.schemas import PromptTechnique


FEW_SHOT_EXAMPLES: dict[PromptTechnique, list[dict[str, str]]] = {
    PromptTechnique.few_shot: [
        {
            "input": "How do I reduce API latency?",
            "output": (
                "1) Measure p95 and p99 first. 2) Add response caching for stable reads. "
                "3) Batch network calls. 4) Move heavy sync work to async workers."
            ),
        },
        {
            "input": "How should I design retries?",
            "output": (
                "Use exponential backoff with jitter, cap max retries, and mark idempotent "
                "operations with request IDs to prevent duplicate side effects."
            ),
        },
    ],
    PromptTechnique.chain_of_thought: [
        {
            "input": "How do I choose a queue system?",
            "output": (
                "Start with workload shape, required delivery guarantees, and ordering needs. "
                "Then map those needs to throughput, partitioning, and operational complexity."
            ),
        }
    ],
    PromptTechnique.step_back: [
        {
            "input": "How do I plan service decomposition?",
            "output": (
                "Step back: group responsibilities by business capability first, not by tables. "
                "Then split services where ownership, deployment cadence, and scaling differ."
            ),
        }
    ],
    PromptTechnique.critique_refine: [
        {
            "input": "How do I improve onboarding conversion?",
            "output": (
                "Initial idea: shorten the signup form. Critique: this alone may reduce data quality. "
                "Refined plan: progressive profiling, intent-based defaults, and a 3-step funnel review."
            ),
        }
    ],
    PromptTechnique.self_consistency: [
        {
            "input": "How should we prioritize roadmap items?",
            "output": (
                "Compare ICE, RICE, and opportunity scoring mentally, then choose one consistent rule "
                "for this quarter and apply it to all initiatives."
            ),
        }
    ],
}
