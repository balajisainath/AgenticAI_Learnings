"""Data models for the evaluation system."""

from pydantic import BaseModel


class EvalCase(BaseModel):
    """A single evaluation test case."""

    question: str
    expected_output: str
    context: str = ""  # optional context/reference for the question


class EvalResult(BaseModel):
    """Result of evaluating a single test case."""

    question: str
    expected_output: str
    actual_output: str
    scores: dict[str, float]  # metric_name -> score (0-1)


class EvalSummary(BaseModel):
    """Summary of an evaluation run."""

    total_cases: int
    average_scores: dict[str, float]
    results: list[EvalResult]
