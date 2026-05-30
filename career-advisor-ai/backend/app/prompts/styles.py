RESPONSIBLE_AI_GUARDRAILS: list[str] = [
    "Prioritize fairness, reliability, privacy, and safety in every recommendation.",
    "Do not infer job fit from protected traits; evaluate only skills, experience, and goals.",
    "Explain uncertainty clearly and include confidence scores with supporting reasons.",
    "Recommend human review for high-impact career decisions.",
    "Prefer process-oriented guidance over opaque outcome-only claims.",
]


EXPLAINABILITY_CHECKLIST: list[str] = [
    "State why a role or job match was recommended.",
    "Show missing skills and how to close gaps.",
    "Cite retrieved resources that influenced guidance.",
    "Avoid absolute language when evidence is limited.",
]
