from app.domain.schemas import PromptStyle, PromptTechnique


STYLE_INSTRUCTIONS: dict[PromptStyle, str] = {
    PromptStyle.concise: "Answer in a compact form with high signal and no filler.",
    PromptStyle.technical: "Use precise technical language and mention tradeoffs explicitly.",
    PromptStyle.socratic: "Ask one clarifying question when useful before giving final guidance.",
    PromptStyle.executive: "Summarize top decisions, impact, and immediate next steps.",
}


TECHNIQUE_INSTRUCTIONS: dict[PromptTechnique, str] = {
    PromptTechnique.zero_shot: "Solve directly from first principles without in-context examples.",
    PromptTechnique.role: "Lean heavily on the persona framing while answering.",
    PromptTechnique.few_shot: "Mimic the format and structure of the provided examples.",
    PromptTechnique.chain_of_thought: (
        "Reason step by step internally, then provide only the final answer and a brief "
        "explicit rationale summary."
    ),
    PromptTechnique.step_back: (
        "Start with a big-picture abstraction, then map it back to concrete guidance."
    ),
    PromptTechnique.critique_refine: (
        "Draft a quick solution mentally, critique weak spots, then provide an improved final answer."
    ),
    PromptTechnique.self_consistency: (
        "Mentally consider multiple candidate answers and return the most consistent one."
    ),
    PromptTechnique.style_variation: (
        "Present the answer in two sections: concise summary and detailed expansion."
    ),
    PromptTechnique.auto: "Use your best judgement to produce the strongest response.",
}
