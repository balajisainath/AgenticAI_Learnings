# 📄 Resume Parser

AI-powered resume parser that extracts structured JSON from resumes using LLM structured output.

## Features

- **Upload** PDF, DOCX, or TXT resumes
- **Extract** name, email, phone, skills, experience, education
- **Structured output** via LangChain `with_structured_output()` + Pydantic schemas
- **Multi-provider** support: OpenAI, Anthropic, Google Gemini
- **Download** parsed JSON

## Tech Stack

| Layer | Tool |
|-------|------|
| LLM | LangChain + `with_structured_output` (Pydantic) |
| Validation | Pydantic v2 strict schemas |
| UI | Streamlit |
| File parsing | PyPDF2, python-docx |

## Quick Start

```bash
# 1. Copy env and add your API key
cp .env.example .env
# edit .env → set OPENAI_API_KEY (or ANTHROPIC/GOOGLE)

# 2. Install & run
cd resume-parser
uv run streamlit run app/main.py
```

Open http://localhost:8501 in your browser.

## How It Works

1. User uploads a resume file
2. Text is extracted from PDF/DOCX/TXT
3. LLM is called with `with_structured_output(ResumeData)` — this constrains the LLM to produce output conforming exactly to the Pydantic schema (uses function calling / tool use under the hood)
4. Validated `ResumeData` object is rendered in the UI and available as JSON download

## Project Structure

```
resume-parser/
├── pyproject.toml
├── .env.example
├── app/
│   ├── main.py          # Streamlit UI
│   ├── config.py        # Settings (pydantic-settings)
│   ├── schemas.py       # Pydantic models for resume data
│   ├── parser.py        # LLM extraction logic
│   ├── llm_factory.py   # Multi-provider LLM factory
│   └── file_reader.py   # PDF/DOCX/TXT reader
```
