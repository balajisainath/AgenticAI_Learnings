# Prompt Testing Playground

A full-stack application to **compare**, **version**, and **track improvements** of LLM prompts. Inspired by prompt versioning best practices from Agenta and prompt debugging methodologies.

## Features

- **Prompt Version Control** — Store v1, v2, v3... of your prompts with full history and notes
- **Side-by-Side Comparison** — Run the same input against multiple prompt versions simultaneously  
- **Quality Tracking** — Rate outputs (1-5 stars), measure latency, track token usage
- **Improvement Analytics** — Visual charts showing how prompt quality evolves across versions
- **Multi-Provider Support** — Works with OpenAI, Anthropic (Claude), and Google (Gemini)
- **Run History** — Full history of every prompt execution with filtering

## Architecture

```
prompt-playground/
├── backend/          # FastAPI + LangChain + SQLite
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── core/         # Config + Database
│   │   ├── domain/       # Pydantic schemas
│   │   └── services/     # LLM execution + comparison logic
│   └── pyproject.toml
└── frontend/         # React + Vite + TailwindCSS
    └── src/
        ├── components/   # UI components
        ├── api.ts        # API client
        └── types.ts      # TypeScript types
```

## Quick Start

### 1. Setup Environment

```bash
cp backend/.env.example backend/.env
# Edit .env → set your API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)
```

### 2. Start Backend

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
# → open http://localhost:5173
```

## How It Works

1. **Create a Prompt** — Give it a name (e.g., "Email Writer", "Code Reviewer")
2. **Add Versions** — Write system prompt + user template with `{{input}}` placeholder
3. **Run Tests** — Enter test input and execute against any version
4. **Rate Outputs** — 1-5 star rating to track quality
5. **Compare** — Select multiple versions, run same input, see outputs side-by-side
6. **Track** — View analytics dashboard showing improvement trends

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/prompts` | List all prompts |
| POST | `/api/v1/prompts` | Create prompt |
| GET | `/api/v1/prompts/:id/versions` | List versions |
| POST | `/api/v1/prompts/:id/versions` | Create new version |
| POST | `/api/v1/run` | Execute prompt |
| PUT | `/api/v1/runs/:id/rate` | Rate a run |
| POST | `/api/v1/compare` | Compare multiple versions |
| GET | `/api/v1/prompts/:id/stats` | Get improvement stats |

## Key Concepts (from research)

- **Prompt Versioning** — Track every change with version numbers, notes, and timestamps
- **Side-by-Side Playground** — Compare outputs visually to see which version performs better
- **Prompt Debugging** — Iterate by changing one variable at a time (system prompt, template, temperature)
- **Quality Metrics** — Human ratings + latency + token cost to make data-driven decisions
