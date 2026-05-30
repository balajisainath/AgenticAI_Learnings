# Backend (FastAPI + LangChain + LangGraph)

## Run Locally

1. Install dependencies with uv:
   - `uv sync`
2. Configure environment:
   - `cp .env.example .env`
   - Set `LLM_PROVIDER` to `openai`, `anthropic`, or `google_genai` (you can also use `gemini`).
   - Add matching provider key:
     - `OPENAI_API_KEY` for OpenAI
     - `ANTHROPIC_API_KEY` for Claude
     - `GOOGLE_API_KEY` for Gemini
3. Start server:
   - `uv run uvicorn app.main:app --reload --port 8000`

## API Endpoints

- `GET /api/v1/health`
- `POST /api/v1/chat/ask`
- `POST /api/v1/chat/compare`
- `GET /api/v1/graph`

Without a provider API key, the service still works using deterministic mock outputs so the full LangGraph flow remains testable.
