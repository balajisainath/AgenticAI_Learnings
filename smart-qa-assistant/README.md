# Smart Q&A Assistant

Production-ready starter for a Prompt Engineering Q&A application built with:

- React + TypeScript (frontend)
- FastAPI (backend API)
- LangChain + LangGraph (prompt workflow engine)

## Features

- Role Prompting with persona selection
- Few-Shot Prompting with reusable curated examples
- Chain-of-Thought Prompting strategy guidance
- Zero-Shot Prompting for direct first-principles responses
- Step-Back Prompting for high-level reframing
- Critique-and-Refine Prompting for iterative improvements
- Self-Consistency Prompting for stable final answers
- Multiple Prompt Styles (concise, technical, socratic, executive)
- LangGraph workflow with execution trace and graph visualization
- Side-by-side comparison of prompt techniques
- Clean modular architecture for frontend and backend

## Project Structure

- `frontend/` React TypeScript client
- `backend/` FastAPI service with LangGraph orchestration

## Quick Start

### 1. Backend

- `cd backend`
- `cp .env.example .env`
- Set `LLM_PROVIDER` in `.env` (`openai`, `anthropic`, `google_genai`, or `gemini`)
- Add the matching provider key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`) for live model calls
- `uv sync`
- `uv run uvicorn app.main:app --reload --port 8000`

### 2. Frontend

- `cd frontend`
- `cp .env.example .env`
- `npm install`
- `npm run dev`

Frontend default URL: http://localhost:5173
Backend default URL: http://localhost:8000

## LangGraph Flow

1. Select strategy dynamically or from explicit user choice.
2. Inject role instruction based on persona.
3. Load few-shot examples when relevant.
4. Build prompt with style + technique directives.
5. Invoke LLM (or mock fallback when no API key is configured).
6. Format response and return trace metadata.
