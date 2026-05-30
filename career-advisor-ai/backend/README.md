# Backend (FastAPI + LangGraph)

## Run Locally (uv)

1. `cp .env.example .env`
2. Configure provider:
   - `LLM_PROVIDER=openai|anthropic|google_genai`
   - Add matching API key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`)
3. Optional deep research:
   - `DEEP_AGENT_ENABLED=true`
   - `TAVILY_API_KEY=...`
4. Install dependencies:
   - `uv sync`
5. Start API server:
   - `uv run uvicorn app.main:app --reload --port 8000`

## Endpoints

- `GET /api/v1/health`
- `POST /api/v1/career/analyze`
- `POST /api/v1/career/chat`
- `POST /api/v1/career/deep-research`
- `GET /api/v1/career/graph`

## Behavior Without API Keys

- If no model API key is configured, chat calls use deterministic fallback responses.
- If deep-agent runtime or key is unavailable, deep-research endpoint falls back to local knowledge retrieval.
