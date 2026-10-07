import { ROUTE_TO_NODE, type AgentNode, type FanEvent, type Route } from "./types";

export type NodeState = "idle" | "live" | "done" | "skipped";

export interface NodeStats {
  state: NodeState;
  calls: number;
  tokens: number;
  cost: number;
  ms: number | null;
}

export type RunStatus = "idle" | "running" | "done" | "failed" | "blocked";

export interface RunView {
  status: RunStatus;
  requestId?: string;
  question?: string;
  /** The model calls were scripted (the UI's Mock switch). */
  mock?: boolean;
  route?: Route;
  reason?: string;
  chosen?: AgentNode;
  nodes: Record<AgentNode, NodeStats>;
  answer?: string;
  sources?: string[];
  totals?: { calls: number; tokens: number; cost: number; latency_ms: number };
  error?: string;
}

const blank = (): NodeStats => ({ state: "idle", calls: 0, tokens: 0, cost: 0, ms: null });

export function emptyRun(): RunView {
  return {
    status: "idle",
    nodes: { supervisor: blank(), stats_guru: blank(), cinema_buff: blank(), out_of_scope: blank() },
  };
}

const AGENT_NODES: AgentNode[] = ["stats_guru", "cinema_buff", "out_of_scope"];

/** Fold the event stream into what the route board and answer card show. */
export function deriveRun(events: FanEvent[]): RunView {
  const run = emptyRun();
  const startedAt: Partial<Record<AgentNode, number>> = {};
  let receivedAt = 0;

  for (const e of events) {
    const t = Date.parse(e.ts);
    const node = e.node as AgentNode;
    run.requestId = e.request_id;

    switch (e.type) {
      case "request.received":
        run.status = "running";
        run.question = e.data.question;
        run.mock = Boolean(e.data.mock);
        run.nodes.supervisor.state = "live";
        receivedAt = t;
        break;
      case "llm.call": {
        const n = run.nodes[node];
        if (!n) break;
        n.calls += 1;
        n.tokens += (e.data.prompt_tokens ?? 0) + (e.data.completion_tokens ?? 0);
        n.cost += e.data.cost ?? 0;
        break;
      }
      case "supervisor.decision": {
        run.route = e.data.route;
        run.reason = e.data.reason;
        run.chosen = ROUTE_TO_NODE[e.data.route as Route] ?? "out_of_scope";
        run.nodes.supervisor.state = "done";
        run.nodes.supervisor.ms = t - receivedAt;
        for (const a of AGENT_NODES) {
          run.nodes[a].state = a === run.chosen ? "live" : "skipped";
        }
        startedAt[run.chosen] = t;
        break;
      }
      case "agent.start":
        if (run.nodes[node]) {
          run.nodes[node].state = "live";
          startedAt[node] = t;
        }
        break;
      case "agent.answer":
        run.answer = e.data.text;
        run.sources = e.data.sources ?? [];
        if (run.nodes[node]) {
          run.nodes[node].state = "done";
          run.nodes[node].ms = t - (startedAt[node] ?? t);
        }
        break;
      case "request.completed":
        run.status = "done";
        run.totals = {
          calls: e.data.llm_calls,
          tokens: e.data.tokens,
          cost: e.data.total_cost,
          latency_ms: e.data.latency_ms,
        };
        break;
      case "budget.blocked":
        run.status = "blocked";
        run.error = e.data.message ?? "Daily budget reached.";
        break;
      case "request.failed":
        run.status = "failed";
        run.error = e.data.message ?? "Something went wrong.";
        break;
    }
  }

  // A stopped request leaves no agent looking busy.
  if (run.status === "failed" || run.status === "blocked") {
    for (const n of Object.values(run.nodes)) if (n.state === "live") n.state = "idle";
  }
  return run;
}
