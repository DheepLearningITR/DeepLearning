# FanDesk — Multi-Agent Demo App (Design Spec)

A light, dockerized full-stack demo for interns. It shows **three agents**: a **supervisor** that routes each question to **one of two specialists**. The route each request takes is visible live in the UI, along with what it cost.

## Constraints
- **Only paid dependency:** an OpenRouter API key. Everything else is free and self-hosted.
- **Model budget:** any tool-calling model at **≤ $1 per million input tokens** on OpenRouter (see §9).
- **One command to run:** `docker compose up --build` starts the whole stack from a clean clone.
- **Keep it light:** 3 containers, no dashboards to maintain. The point is the agents, not the infrastructure.
- **Out of scope:** auth, multi-turn memory, cloud deployment, Prometheus/Grafana.

---

## 1. Concept
Users ask about cricket or movies. The supervisor routes each question to one of these:

| Agent | Handles | Data source | Teaching point |
|---|---|---|---|
| **Stats Guru** | IPL questions | Local SQLite built from Cricsheet IPL open data (ball-by-ball, 2008 onward) | Reasoning over structured data (text-to-SQL) |
| **Cinema Buff** | Movie questions | Wikipedia API (free, no key) | Reasoning over unstructured text (search → read) |
| *(none)* | Anything else | — | Supervisor declines politely |

## 2. Architecture
```
Browser (React) ──SSE──> web (nginx) ──> api (FastAPI)
                                           ├─ Supervisor ─┬─> Stats Guru ──> ipl.db (SQLite, read-only, baked into image)
                                           │              ├─> Cinema Buff ─> Wikipedia API
                                           │              └─> out_of_scope (polite decline)
                                           ├─ LLM calls ──> OpenRouter   (only paid dependency)
                                           ├─ OTLP traces ─> Phoenix
                                           └─ app.db (requests + events, incl. per-LLM-call cost)
```

### API
| Endpoint | Purpose |
|---|---|
| `POST /api/ask` | Runs a request and streams events back as SSE. Frontend reads it with `fetch`, not `EventSource`. |
| `GET /api/requests` | Request history |
| `GET /api/requests/{id}` | One request with all its events (used for replay) |
| `GET /api/spend` | Today's spend vs. budget |
| `GET /health` | Health check |

## 3. Key decisions
- **No agent framework.**
  - Use the OpenAI Python SDK pointed at OpenRouter's OpenAI-compatible endpoint (`https://openrouter.ai/api/v1`).
  - Write a plain agent loop: call model → run tools → return results → repeat until done or step limit.
  - Interns can read the whole loop in one file.
- **The supervisor only routes.**
  - It makes one LLM call with a *forced* tool call `route(route, reason, task)`.
  - `route` must be one of `sports`, `movies` or `out_of_scope`.
  - If the model returns no tool call or an invalid route, **retry once**; if it fails again, treat as `out_of_scope`.
  - The specialist's answer goes straight back to the user, with no extra supervisor call to summarize it.
- **Phoenix for tracing.** One container on SQLite; shows the full agent → LLM → tool tree with tokens, cost and latency. This replaces the need for Prometheus/Grafana in a demo.
- **OpenRouter's reported cost is the source of truth for spend.**
  - Send `extra_body={"usage": {"include": True}}` on every call so the response carries `usage.cost`.
  - The OpenAI SDK keeps this as an extra field, readable as `response.usage.cost`.
  - So the app needs no price tables.

## 4. Agents
| | Supervisor | Stats Guru | Cinema Buff |
|---|---|---|---|
| Job | Pick a route and give a reason | Answer IPL questions | Answer movie questions |
| Model | `SUPERVISOR_MODEL` | `AGENT_MODEL` | `AGENT_MODEL` |
| Tools | `route` (forced) | `get_schema`, `run_sql` | `search_wikipedia`, `get_page_summary` |
| Max LLM calls | 1 (+1 retry) | 5 | 5 |
| Guardrails | Invalid output → retry once → `out_of_scope` | See below | See below |

**Stats Guru guardrails:**
- read-only SQLite connection (`mode=ro`) plus `PRAGMA query_only=ON`;
- SELECT/WITH-only check;
- `LIMIT 50` applied by wrapping: `SELECT * FROM (<query>) LIMIT 50` (never by editing the SQL text);
- 5-second timeout enforced with `conn.set_progress_handler(...)` checking a deadline (`sqlite3`'s `timeout=` is only a lock wait).

**Cinema Buff guardrails:**
- treats page text as data, never as instructions;
- cites the Wikipedia page titles it used;
- caches lookups in memory for 24 hours;
- sends a descriptive User-Agent (`WIKI_USER_AGENT`), as Wikimedia's API policy requires.

**IPL data:** `scripts/load_ipl.py` downloads Cricsheet's IPL CSV archive (`ipl_csv2.zip`) at **image build** and writes `ipl.db` **inside the image** (not in a volume, so a rebuild always ships fresh data).
- The archive has, per match, a ball-by-ball CSV and an `_info.csv` in key/value format. The loader pivots the info files into the `matches` table.
- Tables: `matches`, `deliveries`.
- Views: `batting_stats`, `bowling_stats`, `team_results`.
- **Season normalisation:** Cricsheet stores some seasons as `2007/08`, `2009/10`, `2020/21`. Add an integer `season_year` (the IPL year, e.g. 2008, 2010, 2020) to `matches` and every view; the schema description tells the model to filter on `season_year`.
- **Bowler wickets:** `bowling_stats` counts only wickets credited to the bowler (exclude run out, retired hurt, obstructing the field, etc.).

The views make the model's SQL far more reliable than querying raw ball-by-ball rows. `get_schema` returns the views first.

## 5. Route tracking
Each request gets a `request_id = uuid4().hex` (32 hex chars), also used as the OpenTelemetry trace ID. The backend emits events as it runs. It streams them over SSE and saves them to `app.db`:

1. `request.received`
2. `supervisor.decision` `{route, reason}`
3. `agent.start`
4. `llm.call` `{agent, model, prompt_tokens, completion_tokens, cost, ms, generation_id}`, repeated per LLM call
5. `tool.call` `{name, args}` / `tool.result` `{summary, ms}`, repeated per tool call
6. `agent.answer`
7. `request.completed` `{total_cost, tokens, latency}`

Other events: `budget.blocked`, `request.failed`.

Event shape: `{request_id, seq, ts, type, node, data}`

**UI:**
- **Route board** (plain HTML/CSS, styled as a hand-worked cricket scoreboard): a Supervisor row and one row each for Stats Guru, Cinema Buff and Out of scope. A routing rail and indicator lamps light the path actually taken; unused rows dim and read "Not used". Each row shows calls, tokens, cost and time as number plates that drop in as events arrive.
- **Timeline:** every event with timing, tokens and cost. SQL queries and Wikipedia lookups expand to show details.
- **History page:** replays any past request from its saved events and links to the matching trace in Phoenix.

## 6. Cost
- **Per-call record:** every `llm.call` event (stored in `app.db`) carries agent, model, tokens, cost, latency and OpenRouter generation ID. Spend queries are just sums over these events — no separate ledger table.
- **Answer footer:** each answer shows totals, e.g. *"4 LLM calls · 3,210 tokens · $0.0124 · 6.2 s"*.
- **Budget guard** (checked before every LLM call, using spend so far):
  - if today's spend ≥ `DAILY_BUDGET_USD`, or this request's spend ≥ `MAX_COST_PER_REQUEST_USD`, stop and emit `budget.blocked`.
- **Rough cost:** a question is 2–6 LLM calls of ~2k input tokens each. With Claude Haiku 4.5 ($1 in / $5 out) that's about **$0.01–0.03 per question**; with GPT-5 mini or DeepSeek V3.2 it's a fraction of a cent.
- **Header strip:** today's spend vs. budget.

## 7. Observability
**Traces to Phoenix (OTLP over HTTP, `http://phoenix:6006/v1/traces`):**
- Span tree: `request → supervisor.route → agent.stats_guru → llm / tool.run_sql`.
- The OpenInference instrumentation for the OpenAI SDK creates the LLM spans automatically.
- Create the other spans by hand, using OpenInference span kinds (AGENT, TOOL, CHAIN).
- Attach `route`, `reason` and `cost_usd` as span attributes.

**Logs:** JSON to stdout, with `request_id` on every line.

## 8. Frontend (React + Vite + Tailwind)
The UI must look polished, since it is the face of the demo. Design and build it with the **Impeccable** plugin (`/impeccable`): shape the visual direction first, build, then run its critique/audit/polish passes before calling the frontend done.

- **Ask page:** input box, sample-question chips (the §12 questions), the live route board and timeline, and the answer with its cost footer.
- **History page:** a table of past requests (time, question, route, latency, cost, status). Clicking a row replays its route.
- **Header strip:** today's spend vs. budget, and a link to Phoenix.

## 9. Docker Compose
All ports are bound to localhost.

| Service | What it runs | Port |
|---|---|---|
| `web` | nginx serving the React build and proxying `/api` (SSE settings below) | 8090 (`WEB_PORT`) |
| `api` | FastAPI on uvicorn (single worker), Python 3.12 | internal |
| `phoenix` | `arizephoenix/phoenix` | 6006 |

**nginx SSE settings** for `/api/ask`: `proxy_buffering off`, `proxy_cache off`, `gzip off`, `proxy_read_timeout 300s`, `proxy_http_version 1.1`. FastAPI also sends `X-Accel-Buffering: no` and `Cache-Control: no-cache`.

**Volumes:** `app-data` (`app.db` only), `phoenix-data`.

### `.env`
```
OPENROUTER_API_KEY=
SUPERVISOR_MODEL=openai/gpt-5-nano          # cheap + fast; routing is easy
AGENT_MODEL=anthropic/claude-haiku-4.5      # reliable tool use; $1 in / $5 out
DAILY_BUDGET_USD=1.00
MAX_COST_PER_REQUEST_USD=0.10
MOCK_LLM=false               # true = scripted responses, no OpenRouter calls
WIKI_USER_AGENT=FanDesk-Demo/1.0 (contact: <email>)
PHOENIX_URL=http://localhost:6006
```

**Choosing models:** any OpenRouter model that supports `tools` and `tool_choice` and costs ≤ $1 per million input tokens. Model IDs live only in `.env`, never in code. Good alternatives as of Oct 2026 (input / output per 1M tokens):

| Model | In | Out | Note |
|---|---|---|---|
| `anthropic/claude-haiku-4.5` | $1.00 | $5.00 | Default agent model; at the cap |
| `openai/gpt-5-mini` | $0.25 | $2.00 | Strong, cheaper agent option |
| `deepseek/deepseek-v3.2` | $0.28 | $0.42 | Cheapest capable agent option |
| `google/gemini-2.5-flash-lite` | $0.10 | $0.40 | Good supervisor option |
| `openai/gpt-5-nano` | $0.05 | $0.40 | Default supervisor model |

Sonnet is over budget (Sonnet 5.5 is $2 / $10). Prices change — check OpenRouter's models page before a demo.

**`MOCK_LLM=true`:** returns scripted responses keyed on the six §12 questions (anything else gets a generic out-of-scope reply), so the full demo — route board, timeline, history, traces — runs end to end with no API key.

## 10. Repo layout
```
fandesk/
├─ docker-compose.yml   .env.example   README.md
├─ backend/   app/{main, orchestrator, llm, events, spend, telemetry, store}.py
│             app/agents/{supervisor, stats_guru, cinema_buff}.py
│             app/tools/{sql_tools, wiki_tools}.py   scripts/load_ipl.py   tests/
├─ frontend/  src/pages/{Ask, History}  src/components/{RouteGraph, Timeline, CostStrip}
└─ web/       nginx.conf
```

## 11. Build order
1. Backend orchestrator and agents with `MOCK_LLM=true`, plus the event stream and SQLite store.
2. The IPL loader and SQL tools, then the Wikipedia tools. Unit-test each tool on its own (incl. `season_year`, the SQL guardrails and the timeout).
3. Real OpenRouter calls, cost capture and the budget guard.
4. Frontend: the Ask page with the live route board first, then History.
5. Phoenix traces.
6. Compose: `docker compose up --build` works from a clean clone.

## 12. Acceptance tests (also the demo script)
| Question | Expected route | Pass condition |
|---|---|---|
| Top 5 run-scorers for CSK across all IPL seasons? | Stats Guru | Correct top 5 from `batting_stats` |
| Who took the most wickets in IPL 2023? | Stats Guru | Filters on `season_year = 2023`; bowler wickets only |
| Who directed Vikram (2022) and what's it about? | Cinema Buff | Names Lokesh Kanagaraj; cites the page |
| Suggest movies about cricket like Lagaan | Cinema Buff | Routes to movies despite the cricket mention |
| Tell me about Dhoni | Ambiguous | Either specialist passes, as long as the routing reason is shown |
| Write me a poem about rain | Out of scope | 1 LLM call, no specialist |

**Every request must also:**
- show its route live in the UI;
- appear in History;
- appear as a trace in Phoenix;
- show its cost in the answer footer and the header strip.

## References
- OpenRouter usage accounting (cost in responses): https://openrouter.ai/docs/use-cases/usage-accounting
- OpenRouter models & pricing: https://openrouter.ai/models
- Phoenix self-hosting: https://arize.com/docs/phoenix/self-hosting
- Cricsheet downloads: https://cricsheet.org/downloads/
