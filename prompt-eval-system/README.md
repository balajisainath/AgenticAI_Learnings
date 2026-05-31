# 📊 Prompt Evaluation System

A minimal prompt evaluation system that scores LLM outputs against expected answers using [DeepEval](https://github.com/confident-ai/deepeval) metrics.

## Features

- **Input Dataset**: Load test cases (questions + expected outputs) via JSON, CSV, or manual entry
- **Prompt Templates**: Test different prompt templates with `{question}` placeholder
- **Scoring Metrics**: Evaluate using multiple metrics:
  - **Correctness** – Is the output factually correct vs expected?
  - **Relevancy** – Is the answer relevant to the question?
  - **Coherence** – Is the output well-structured and clear?
  - **Completeness** – Does it cover all key points?
- **Visual Dashboard**: Bar charts, radar plots, and detailed result tables
- **Export Results**: Download evaluation results as JSON

## Tech Stack

- **Backend**: Python, LangChain, DeepEval
- **Frontend**: Streamlit
- **LLM Providers**: OpenAI, Anthropic, Google Gemini
- **Charts**: Plotly

## Quick Start

```bash
# 1. Copy and fill in your API key
cp .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-...

# 2. Install dependencies
uv sync

# 3. Run the app
uv run streamlit run app/main.py --server.port 8501
```

Open http://localhost:8501 in your browser.

## Project Structure

```
prompt-eval-system/
├── pyproject.toml          # Dependencies
├── .env.example            # Environment template
├── data/
│   └── sample_dataset.json # Sample eval dataset
└── app/
    ├── __init__.py
    ├── main.py             # Streamlit UI
    ├── config.py           # Settings (pydantic-settings)
    ├── schemas.py          # Data models
    ├── llm_factory.py      # LLM provider factory
    └── evaluator.py        # Evaluation logic (DeepEval)
```

## How It Works

1. **Define a prompt template** with a `{question}` placeholder
2. **Load test cases** – each has a question, expected output, and optional context
3. **Select metrics** – choose which scoring dimensions to evaluate
4. **Run evaluation** – the system sends each question through the LLM and scores the output against the expected answer using DeepEval's metrics
5. **View results** – see scores in charts and detailed tables

## Sample Dataset

A sample dataset with 8 general knowledge questions is included at `data/sample_dataset.json`. You can also download it from the app's Dataset tab.
