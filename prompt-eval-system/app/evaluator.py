"""Evaluation service – runs prompts through LLM and scores outputs."""

from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    GEval,
)
from deepeval.test_case import LLMTestCase

from app.config import get_settings
from app.llm_factory import get_llm
from app.schemas import EvalCase, EvalResult, EvalSummary


def _generate_output(prompt_template: str, question: str) -> str:
    """Run a question through the LLM with the given prompt template."""
    llm = get_llm()
    full_prompt = prompt_template.format(question=question)
    response = llm.invoke(full_prompt)
    return response.content


def _score_case(
    question: str,
    expected: str,
    actual: str,
    context: str,
    metrics: list[str],
) -> dict[str, float]:
    """Score a single test case using deepeval metrics."""
    settings = get_settings()
    scores: dict[str, float] = {}

    # Build the deepeval test case
    test_case = LLMTestCase(
        input=question,
        actual_output=actual,
        expected_output=expected,
        retrieval_context=[context] if context else None,
    )

    for metric_name in metrics:
        try:
            metric = _get_metric(metric_name, settings)
            metric.measure(test_case)
            score = metric.score if metric.score is not None else 0.0
            scores[metric_name] = round(float(score), 4)
        except Exception:
            scores[metric_name] = 0.0

    return scores


def _get_metric(name: str, settings):
    """Instantiate a deepeval metric by name."""
    model = settings.openai_model

    match name:
        case "correctness":
            return GEval(
                name="Correctness",
                criteria=(
                    "Determine whether the actual output is factually correct "
                    "based on the expected output."
                ),
                evaluation_params=[
                    "input",
                    "actual_output",
                    "expected_output",
                ],
                model=model,
            )
        case "relevancy":
            return AnswerRelevancyMetric(model=model, threshold=0.5)
        case "faithfulness":
            return FaithfulnessMetric(model=model, threshold=0.5)
        case "coherence":
            return GEval(
                name="Coherence",
                criteria=(
                    "Determine whether the actual output is coherent, "
                    "well-structured, and easy to understand."
                ),
                evaluation_params=["actual_output"],
                model=model,
            )
        case "completeness":
            return GEval(
                name="Completeness",
                criteria=(
                    "Determine whether the actual output covers all key points "
                    "mentioned in the expected output."
                ),
                evaluation_params=[
                    "input",
                    "actual_output",
                    "expected_output",
                ],
                model=model,
            )
        case _:
            # Default to a generic GEval with custom criteria
            return GEval(
                name=name.capitalize(),
                criteria=f"Evaluate the {name} of the actual output.",
                evaluation_params=["input", "actual_output"],
                model=model,
            )


def run_evaluation(
    prompt_template: str,
    eval_cases: list[EvalCase],
    metrics: list[str] | None = None,
) -> EvalSummary:
    """Run a full evaluation across all test cases.

    Args:
        prompt_template: The prompt template with {question} placeholder.
        eval_cases: List of test cases to evaluate.
        metrics: List of metric names to compute. Defaults to correctness + relevancy.

    Returns:
        EvalSummary with all results and average scores.
    """
    if metrics is None:
        metrics = ["correctness", "relevancy"]

    results: list[EvalResult] = []

    for case in eval_cases:
        # Generate LLM output
        actual_output = _generate_output(prompt_template, case.question)

        # Score the output
        scores = _score_case(
            question=case.question,
            expected=case.expected_output,
            actual=actual_output,
            context=case.context,
            metrics=metrics,
        )

        results.append(
            EvalResult(
                question=case.question,
                expected_output=case.expected_output,
                actual_output=actual_output,
                scores=scores,
            )
        )

    # Compute averages
    avg_scores: dict[str, float] = {}
    for metric_name in metrics:
        metric_scores = [r.scores.get(metric_name, 0.0) for r in results]
        if metric_scores:
            avg_scores[metric_name] = round(
                sum(metric_scores) / len(metric_scores), 4
            )

    return EvalSummary(
        total_cases=len(results),
        average_scores=avg_scores,
        results=results,
    )
