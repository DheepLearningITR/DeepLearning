# FanDesk

A multi-agent demo: a **supervisor** routes each question to **Stats Guru** (IPL stats, SQL over Cricsheet data) or **Cinema Buff** (movies, Wikipedia), or declines it. The route board shows the path live, with tokens, cost and time for every step.

Design spec: `../fandesk-design.md`.

## Run everything (Docker)

```bash
cp .env.example .env        # paste your OPENROUTER_API_KEY
docker compose up --build
```

- App: http://localhost:8090 (set `WEB_PORT` in `.env` to change it)
- Phoenix traces: http://localhost:6006

The first build downloads Cricsheet's IPL archive and bakes `ipl.db` into the API image. Rebuild to refresh the data.

## Live / Mock switch

The header has a **Model: Live / Mock** switch.

- **Live**: real model calls through OpenRouter. These count against `DAILY_BUDGET_USD`.
- **Mock**: scripted model replies for the six sample questions. The SQL still runs against the real IPL database and Wikipedia is still called live. Nothing is spent.

With no API key, the switch is locked to Mock. `MOCK_LLM` in `.env` sets where the switch starts.

## Develop without Docker

Backend (Python 3.12+):

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/load_ipl.py --out data/ipl.db
uvicorn app.main:app --port 8000
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api to :8000
```

`VITE_USE_MOCK_STREAM=true npm run dev` runs the UI alone with an in-browser scripted stream, for design work without the backend.

## Layout

```
backend/   app/{main, orchestrator, llm, mock_llm, events, store, telemetry, config}.py
           app/agents/{supervisor, stats_guru, cinema_buff, loop}.py
           app/tools/{sql_tools, wiki_tools}.py   scripts/load_ipl.py   tests/
frontend/  src/pages/{Ask, History}   src/components/{RouteBoard, Timeline, CostStrip, ...}
```
