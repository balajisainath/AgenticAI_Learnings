"""Prompt Evaluation System – Streamlit UI."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.evaluator import run_evaluation
from app.schemas import EvalCase, EvalSummary

# Page config
st.set_page_config(
    page_title="Prompt Eval System",
    layout="wide",
)

# Styling
st.markdown(
    """
    <style>
    .block-container { max-width: 1200px; padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.title("Prompt Evaluation System")
st.caption(
    "Evaluate your prompts against a dataset with scoring metrics powered by DeepEval."
)

# Sidebar
with st.sidebar:
    st.header("Configuration")

    # Provider selection
    provider = st.selectbox(
        "LLM Provider",
        ["openai", "anthropic", "google"],
        index=0,
    )

    # API key input
    api_key = st.text_input(
        f"{provider.capitalize()} API Key",
        type="password",
        help="Enter your API key for the selected provider",
    )

    # Metrics selection
    st.subheader("Metrics")
    available_metrics = [
        "correctness",
        "relevancy",
        "coherence",
        "completeness",
    ]
    selected_metrics = st.multiselect(
        "Select metrics to evaluate",
        available_metrics,
        default=["correctness", "relevancy"],
    )

    st.divider()
    st.markdown("**Tips:**")
    st.markdown("- Use `{question}` placeholder in your prompt template")
    st.markdown("- Upload a JSON/CSV dataset or use manual input")
    st.markdown("- More metrics = longer eval time")

# Set env vars from sidebar input
if api_key:
    key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    os.environ[key_map[provider]] = api_key
    os.environ["LLM_PROVIDER"] = provider

# Main content
tab1, tab2, tab3 = st.tabs(["Setup & Run", "Results", "Dataset"])

# Tab 1: Setup
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Prompt Template")
        prompt_template = st.text_area(
            "Enter your prompt template",
            value="Answer the following question concisely and accurately.\n\nQuestion: {question}\n\nAnswer:",
            height=200,
            help="Use {question} as a placeholder for the input question.",
        )

    with col2:
        st.subheader("Dataset Input")
        input_method = st.radio(
            "Input method",
            ["Manual", "Upload JSON", "Upload CSV"],
            horizontal=True,
        )

        if input_method == "Manual":
            st.markdown("Add test cases below:")
            num_cases = st.number_input(
                "Number of test cases", min_value=1, max_value=20, value=3
            )

            cases: list[dict] = []
            for i in range(int(num_cases)):
                with st.expander(f"Test Case {i + 1}", expanded=(i == 0)):
                    q = st.text_input(f"Question #{i + 1}", key=f"q_{i}")
                    e = st.text_area(f"Expected Output #{i + 1}", key=f"e_{i}")
                    c = st.text_input(
                        f"Context (optional) #{i + 1}", key=f"c_{i}"
                    )
                    if q and e:
                        cases.append(
                            {"question": q, "expected_output": e, "context": c}
                        )

        elif input_method == "Upload JSON":
            uploaded = st.file_uploader(
                "Upload JSON dataset",
                type=["json"],
                help='Format: [{"question": "...", "expected_output": "...", "context": "..."}]',
            )
            cases = []
            if uploaded:
                try:
                    cases = json.loads(uploaded.getvalue().decode())
                    st.success(f"Loaded {len(cases)} test cases")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format")

        elif input_method == "Upload CSV":
            uploaded = st.file_uploader(
                "Upload CSV dataset",
                type=["csv"],
                help="Columns: question, expected_output, context (optional)",
            )
            cases = []
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    cases = df.to_dict("records")
                    st.success(f"Loaded {len(cases)} test cases")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")

    st.divider()

    # Run evaluation button
    if st.button("Run Evaluation", type="primary", width="stretch"):
        if not api_key:
            st.error("Please enter your API key in the sidebar.")
        elif not cases:
            st.error("Please add at least one test case.")
        elif "{question}" not in prompt_template:
            st.error("Prompt template must contain {question} placeholder.")
        else:
            eval_cases = [EvalCase(**c) for c in cases]

            with st.spinner("Running evaluation... This may take a minute."):
                try:
                    # Clear cached settings to pick up new env vars
                    from app.config import get_settings

                    get_settings.cache_clear()

                    summary = run_evaluation(
                        prompt_template=prompt_template,
                        eval_cases=eval_cases,
                        metrics=selected_metrics,
                    )
                    st.session_state["eval_summary"] = summary
                    st.success(
                        f"Evaluation complete! {summary.total_cases} cases evaluated."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")

# Tab 2: Results
with tab2:
    if "eval_summary" not in st.session_state:
        st.info("Run an evaluation first to see results here.")
    else:
        summary: EvalSummary = st.session_state["eval_summary"]

        # Metric summary cards
        st.subheader("Average Scores")
        cols = st.columns(len(summary.average_scores))
        for i, (metric, score) in enumerate(summary.average_scores.items()):
            with cols[i]:
                st.metric(
                    label=metric.capitalize(),
                    value=f"{score:.1%}",
                )

        st.divider()

        # Bar chart of scores
        st.subheader("Score Distribution")
        chart_data = []
        for result in summary.results:
            for metric, score in result.scores.items():
                if "_error" not in metric:
                    chart_data.append(
                        {
                            "Question": result.question[:50] + "..."
                            if len(result.question) > 50
                            else result.question,
                            "Metric": metric.capitalize(),
                            "Score": score,
                        }
                    )

        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            fig = px.bar(
                df_chart,
                x="Question",
                y="Score",
                color="Metric",
                barmode="group",
                title="Scores by Question & Metric",
            )
            fig.update_layout(yaxis_range=[0, 1])
            st.plotly_chart(fig, width="stretch")

        # Radar chart for average scores
        if len(summary.average_scores) >= 3:
            st.subheader("Metric Radar")
            categories = list(summary.average_scores.keys())
            values = list(summary.average_scores.values())
            values.append(values[0])  # close the polygon

            fig_radar = go.Figure(
                data=go.Scatterpolar(
                    r=values,
                    theta=categories + [categories[0]],
                    fill="toself",
                    name="Average Scores",
                )
            )
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=False,
            )
            st.plotly_chart(fig_radar, width="stretch")

        st.divider()

        # Detailed results table
        st.subheader("Detailed Results")
        for i, result in enumerate(summary.results):
            with st.expander(
                f"Case {i + 1}: {result.question[:80]}", expanded=False
            ):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Expected Output:**")
                    st.text(result.expected_output)
                with col_b:
                    st.markdown("**Actual Output:**")
                    st.text(result.actual_output)

                st.markdown("**Scores:**")
                score_cols = st.columns(len(result.scores))
                for j, (metric, score) in enumerate(result.scores.items()):
                    if "_error" not in metric:
                        with score_cols[j % len(score_cols)]:
                            st.metric(metric.capitalize(), f"{score:.1%}")

        # Export results
        st.divider()
        if st.button("Export Results as JSON"):
            export_data = summary.model_dump()
            st.download_button(
                "Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name="eval_results.json",
                mime="application/json",
            )

# Tab 3: Dataset
with tab3:
    st.subheader("Sample Dataset")
    st.markdown("Download a sample dataset to get started:")

    sample_data = [
        {
            "question": "What is the capital of France?",
            "expected_output": "The capital of France is Paris.",
            "context": "France is a country in Western Europe.",
        },
        {
            "question": "What is photosynthesis?",
            "expected_output": "Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into glucose and oxygen.",
            "context": "Biology - plant processes",
        },
        {
            "question": "Who wrote Romeo and Juliet?",
            "expected_output": "William Shakespeare wrote Romeo and Juliet.",
            "context": "English literature",
        },
        {
            "question": "What is the speed of light?",
            "expected_output": "The speed of light in a vacuum is approximately 299,792,458 meters per second (about 3 x 10^8 m/s).",
            "context": "Physics - electromagnetic radiation",
        },
        {
            "question": "Explain the water cycle in simple terms.",
            "expected_output": "The water cycle is the continuous movement of water: it evaporates from surfaces, rises to form clouds (condensation), falls as precipitation (rain/snow), and flows back to oceans and lakes through rivers and groundwater.",
            "context": "Earth science - hydrology",
        },
    ]

    st.json(sample_data)

    st.download_button(
        "Download Sample Dataset (JSON)",
        data=json.dumps(sample_data, indent=2),
        file_name="sample_eval_dataset.json",
        mime="application/json",
    )

    st.divider()
    st.subheader("CSV Format")
    st.markdown("You can also use CSV format with these columns:")
    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df, width="stretch")

    st.download_button(
        "Download Sample Dataset (CSV)",
        data=sample_df.to_csv(index=False),
        file_name="sample_eval_dataset.csv",
        mime="text/csv",
    )
