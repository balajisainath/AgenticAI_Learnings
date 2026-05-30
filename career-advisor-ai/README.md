# Career Advisor AI (Course Project)

Career Advisor AI is a practical, production-style project built with:

- React + TypeScript + Vite (frontend)
- FastAPI (backend)
- LangChain + LangGraph (multi-agent orchestration)
- Lightweight RAG (in-memory vector retrieval)
- Optional Deep-Agent research mode with graceful fallback

This project is intentionally scoped for learning: no full deployment pipeline and no test suite required.

## What It Does

- Profile Analysis Agent: normalizes profile signals and builds summary context
- RAG Retriever Agent: fetches relevant jobs/courses/resources from local knowledge base
- Career Recommendation Agent: ranks best-fit roles with confidence and rationale
- Job Matching Agent: scores profile against curated job postings
- Roadmap Generation Agent: creates phase-wise upskilling roadmap
- Resume Analysis Agent: reviews resume quality and rewrite guidance
- Safety/Bias Detection Agent: applies risk flags and transparency checks
- Memory Agent: stores short session memory notes across requests

Also includes:

- Career coach chat endpoint
- Graph view of agent execution + trace details
- Optional deep-research endpoint that uses deep agents when available, and falls back to local retrieval when unavailable

## Project Structure

- `backend/` FastAPI + LangGraph service
- `frontend/` React TypeScript dashboard

## Quick Start

### 1) Run backend (uv)

- `cd backend`
- `cp .env.example .env`
- Add provider key for your selected model provider:
  - `OPENAI_API_KEY` or
  - `ANTHROPIC_API_KEY` or
  - `GOOGLE_API_KEY`
- Optional for deep web research: set `DEEP_AGENT_ENABLED=true` and `TAVILY_API_KEY=...`
- `uv sync`
- `uv run uvicorn app.main:app --reload --port 8000`

### 2) Run frontend

- `cd frontend`
- `cp .env.example .env`
- `npm install`
- `npm run dev`

Default URLs:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Main API Endpoints

- `GET /api/v1/health`
- `POST /api/v1/career/analyze`
- `POST /api/v1/career/chat`
- `POST /api/v1/career/deep-research`
- `GET /api/v1/career/graph`

## Notes on Deep Agents

- Deep-agent support is optional and dynamically loaded at runtime.
- If deep-agent runtime/dependencies are unavailable, the endpoint still returns useful results using local RAG fallback mode.
