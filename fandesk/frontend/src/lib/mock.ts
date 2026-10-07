// In-browser stand-in for the backend, so the UI can be designed and demoed
// before the API exists. Plays scripted event streams for the six demo
// questions (fandesk-design.md §12). Figures are illustrative, not live data.
import type { EventData, EventNode, EventType, FanEvent, RequestSummary, Route } from "./types";

type Step = { wait: number; type: EventType; node: EventNode; data: EventData };

const SUP_MODEL = "openai/gpt-5-nano";
const AGENT_MODEL = "anthropic/claude-haiku-4.5";

const step = (wait: number, type: EventType, node: EventNode, data: EventData = {}): Step => ({
  wait,
  type,
  node,
  data,
});

const supLlm = (ms: number, pt: number, ct: number) =>
  step(ms, "llm.call", "supervisor", {
    model: SUP_MODEL,
    prompt_tokens: pt,
    completion_tokens: ct,
    cost: (pt * 0.05 + ct * 0.4) / 1e6,
    ms,
  });

const agentLlm = (node: EventNode, ms: number, pt: number, ct: number) =>
  step(ms, "llm.call", node, {
    model: AGENT_MODEL,
    prompt_tokens: pt,
    completion_tokens: ct,
    cost: (pt * 1 + ct * 5) / 1e6,
    ms,
  });

const tool = (node: EventNode, name: string, args: EventData, summary: string, ms: number, extra: EventData = {}) => [
  step(120, "tool.call", node, { name, args }),
  step(ms, "tool.result", node, { name, summary, ms, ...extra }),
];

const decide = (route: Route, reason: string, task: string) =>
  step(140, "supervisor.decision", "supervisor", { route, reason, task });

interface Script {
  match: RegExp;
  steps: Step[];
}

const SCRIPTS: Script[] = [
  {
    match: /csk|run-?scorers/i,
    steps: [
      supLlm(820, 640, 61),
      decide("sports", "Asks for IPL batting totals for one franchise, which is structured stats data.", "Top 5 run-scorers for Chennai Super Kings, all seasons"),
      step(150, "agent.start", "stats_guru"),
      agentLlm("stats_guru", 1250, 1810, 52),
      ...tool("stats_guru", "get_schema", {}, "3 views, 2 tables", 14),
      agentLlm("stats_guru", 1480, 2460, 121),
      ...tool(
        "stats_guru",
        "run_sql",
        {
          sql: "SELECT batter, SUM(runs) AS runs\nFROM batting_stats\nWHERE team = 'Chennai Super Kings'\nGROUP BY batter\nORDER BY runs DESC\nLIMIT 5",
        },
        "5 rows",
        46,
      ),
      agentLlm("stats_guru", 1720, 2710, 168),
      step(90, "agent.answer", "stats_guru", {
        text: "Chennai Super Kings' top 5 run-scorers across all IPL seasons:\n1. Suresh Raina — 4,687 runs\n2. MS Dhoni — 4,669 runs\n3. Faf du Plessis — 2,721 runs\n4. Ruturaj Gaikwad — 2,380 runs\n5. Murali Vijay — 1,708 runs",
        sources: ["ipl.db · batting_stats"],
      }),
    ],
  },
  {
    match: /wickets.*2023|2023.*wickets/i,
    steps: [
      supLlm(760, 628, 57),
      decide("sports", "A season-level bowling record from the IPL, answerable from the stats database.", "Most wickets in IPL 2023"),
      step(150, "agent.start", "stats_guru"),
      agentLlm("stats_guru", 1180, 1790, 49),
      ...tool("stats_guru", "get_schema", {}, "3 views, 2 tables", 12),
      agentLlm("stats_guru", 1390, 2440, 109),
      ...tool(
        "stats_guru",
        "run_sql",
        {
          sql: "SELECT bowler, team, SUM(wickets) AS wickets\nFROM bowling_stats\nWHERE season_year = 2023\nGROUP BY bowler, team\nORDER BY wickets DESC\nLIMIT 3",
        },
        "3 rows",
        38,
      ),
      agentLlm("stats_guru", 1510, 2620, 97),
      step(90, "agent.answer", "stats_guru", {
        text: "Mohammed Shami took the most wickets in IPL 2023: 28 for Gujarat Titans. Mohit Sharma and Rashid Khan were next with 27 each.",
        sources: ["ipl.db · bowling_stats"],
      }),
    ],
  },
  {
    match: /vikram/i,
    steps: [
      supLlm(790, 631, 59),
      decide("movies", "Asks who directed a film and what it is about: a movie question.", "Director and plot of Vikram (2022)"),
      step(150, "agent.start", "cinema_buff"),
      agentLlm("cinema_buff", 1120, 1520, 44),
      ...tool("cinema_buff", "search_wikipedia", { query: "Vikram 2022 film" }, "5 results", 410),
      agentLlm("cinema_buff", 980, 1890, 38),
      ...tool("cinema_buff", "get_page_summary", { title: "Vikram (2022 film)" }, "1,240 characters", 380),
      agentLlm("cinema_buff", 1650, 2380, 146),
      step(90, "agent.answer", "cinema_buff", {
        text: "Vikram (2022) was written and directed by Lokesh Kanagaraj. It is a Tamil action thriller starring Kamal Haasan, Vijay Sethupathi and Fahadh Faasil: a black-ops team investigates a series of masked killings, which leads them to a drug syndicate and an agent everyone believed was dead.",
        sources: ["Vikram (2022 film)"],
      }),
    ],
  },
  {
    match: /lagaan/i,
    steps: [
      supLlm(840, 636, 66),
      decide("movies", "Mentions cricket, but the task is recommending films, so it is a movie question.", "Movies about cricket similar to Lagaan"),
      step(150, "agent.start", "cinema_buff"),
      agentLlm("cinema_buff", 1090, 1500, 41),
      ...tool("cinema_buff", "search_wikipedia", { query: "Indian cricket sports drama film" }, "8 results", 450),
      agentLlm("cinema_buff", 1040, 2010, 63),
      ...tool("cinema_buff", "get_page_summary", { title: "Iqbal (film)" }, "980 characters", 340),
      ...tool("cinema_buff", "get_page_summary", { title: "83 (film)" }, "1,110 characters", 360),
      agentLlm("cinema_buff", 1820, 2790, 184),
      step(90, "agent.answer", "cinema_buff", {
        text: "If you liked Lagaan, try:\n1. Iqbal (2005): a deaf village boy chases a place in the Indian team.\n2. 83 (2021): the story of India's 1983 World Cup win.\n3. M.S. Dhoni: The Untold Story (2016): Dhoni's road from Ranchi to captain.\n4. Jersey (2019): a former cricketer returns to the game in his thirties.",
        sources: ["Iqbal (film)", "83 (film)"],
      }),
    ],
  },
  {
    match: /dhoni/i,
    steps: [
      supLlm(910, 622, 74),
      decide("sports", "Dhoni most likely means MS Dhoni the cricketer, whose IPL record is in the stats database. A question about the Dhoni film would go to Cinema Buff.", "IPL career summary for MS Dhoni"),
      step(150, "agent.start", "stats_guru"),
      agentLlm("stats_guru", 1200, 1800, 50),
      ...tool("stats_guru", "get_schema", {}, "3 views, 2 tables", 13),
      agentLlm("stats_guru", 1430, 2450, 126),
      ...tool(
        "stats_guru",
        "run_sql",
        {
          sql: "SELECT COUNT(DISTINCT match_id) AS matches,\n       SUM(runs) AS runs,\n       ROUND(100.0 * SUM(runs) / SUM(balls), 1) AS strike_rate\nFROM batting_stats\nWHERE batter = 'MS Dhoni'",
        },
        "1 row",
        41,
      ),
      agentLlm("stats_guru", 1560, 2650, 118),
      step(90, "agent.answer", "stats_guru", {
        text: "MS Dhoni has played 264 IPL matches, scoring 5,243 runs at a strike rate of 137.5, almost all for Chennai Super Kings, whom he captained to five titles.",
        sources: ["ipl.db · batting_stats"],
      }),
    ],
  },
  {
    match: /poem|rain/i,
    steps: [
      supLlm(700, 618, 48),
      decide("out_of_scope", "Creative writing is neither IPL cricket nor movies.", "Write a poem about rain"),
      step(220, "agent.answer", "out_of_scope", {
        text: "I can only help with IPL cricket stats and movies. Try asking about a season, a player or a film.",
        sources: [],
      }),
    ],
  },
];

const FALLBACK: Step[] = [
  supLlm(700, 610, 52),
  decide("out_of_scope", "Mock mode only has scripted answers for the six sample questions.", "Unscripted question"),
  step(220, "agent.answer", "out_of_scope", {
    text: "This preview is running in mock mode, so it can only answer the sample questions. Pick one of the chips above.",
    sources: [],
  }),
];

export const SAMPLE_QUESTIONS = [
  "Top 5 run-scorers for CSK across all IPL seasons?",
  "Who took the most wickets in IPL 2023?",
  "Who directed Vikram (2022) and what's it about?",
  "Suggest movies about cricket like Lagaan",
  "Tell me about Dhoni",
  "Write me a poem about rain",
];

const BUDGET_USD = 1.0;

interface Stored {
  summary: RequestSummary;
  events: FanEvent[];
}
const store: Stored[] = [];

const newId = () => crypto.randomUUID().replace(/-/g, "");
const sleep = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(t);
      reject(new DOMException("Aborted", "AbortError"));
    });
  });

function summarise(id: string, question: string, events: FanEvent[]): RequestSummary {
  const done = events.find((e) => e.type === "request.completed");
  const decision = events.find((e) => e.type === "supervisor.decision");
  return {
    id,
    question,
    route: decision?.data.route ?? null,
    status: done ? "completed" : "running",
    created_at: events[0].ts,
    latency_ms: done?.data.latency_ms ?? 0,
    cost_usd: done?.data.total_cost ?? 0,
    tokens: done?.data.tokens ?? 0,
    llm_calls: done?.data.llm_calls ?? 0,
    mock: true,
  };
}

/** Builds the full event list for a script, timestamped from `start`. */
function build(question: string, start: number): { id: string; events: FanEvent[]; waits: number[] } {
  const steps = (SCRIPTS.find((s) => s.match.test(question)) ?? { steps: FALLBACK }).steps;
  const id = newId();
  let t = start;
  let seq = 0;
  const events: FanEvent[] = [];
  const waits: number[] = [];
  const push = (wait: number, type: EventType, node: EventNode, data: EventData) => {
    t += wait;
    waits.push(wait);
    events.push({ request_id: id, seq: seq++, ts: new Date(t).toISOString(), type, node, data });
  };

  push(0, "request.received", "user", { question, mock: true });
  for (const s of steps) push(s.wait, s.type, s.node, s.data);

  const llm = events.filter((e) => e.type === "llm.call");
  push(60, "request.completed", "response", {
    llm_calls: llm.length,
    tokens: llm.reduce((a, e) => a + e.data.prompt_tokens + e.data.completion_tokens, 0),
    total_cost: llm.reduce((a, e) => a + e.data.cost, 0),
    latency_ms: t + 60 - start,
  });
  return { id, events, waits };
}

// A few earlier runs so History isn't empty on first load.
(() => {
  const base = Date.now() - 1000 * 60 * 47;
  [SAMPLE_QUESTIONS[2], SAMPLE_QUESTIONS[0], SAMPLE_QUESTIONS[5]].forEach((q, i) => {
    const { id, events } = build(q, base + i * 1000 * 60 * 9);
    store.unshift({ summary: summarise(id, q, events), events });
  });
})();

export async function mockAsk(question: string, onEvent: (e: FanEvent) => void, signal?: AbortSignal) {
  const { id, events, waits } = build(question, Date.now());
  const entry: Stored = { summary: summarise(id, question, events.slice(0, 1)), events: [] };
  store.unshift(entry);
  for (let i = 0; i < events.length; i++) {
    await sleep(waits[i], signal);
    const e = { ...events[i], ts: new Date().toISOString() };
    entry.events.push(e);
    onEvent(e);
  }
  entry.summary = summarise(id, question, entry.events);
}

export async function mockListRequests(): Promise<RequestSummary[]> {
  return store.map((s) => s.summary);
}

export async function mockGetRequest(id: string): Promise<FanEvent[]> {
  return store.find((s) => s.summary.id === id)?.events ?? [];
}

export async function mockSpend() {
  const spent = store.reduce((a, s) => a + s.summary.cost_usd, 0);
  return { spent_usd: spent, budget_usd: BUDGET_USD };
}
