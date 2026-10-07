// Mirrors the backend event contract (fandesk-design.md §5).

export type EventType =
  | "request.received"
  | "supervisor.decision"
  | "agent.start"
  | "llm.call"
  | "tool.call"
  | "tool.result"
  | "agent.answer"
  | "request.completed"
  | "budget.blocked"
  | "request.failed";

export type AgentNode = "supervisor" | "stats_guru" | "cinema_buff" | "out_of_scope";
export type EventNode = AgentNode | "user" | "response";
export type Route = "sports" | "movies" | "out_of_scope";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type EventData = Record<string, any>;

export interface FanEvent {
  request_id: string;
  seq: number;
  ts: string;
  type: EventType;
  node: EventNode;
  data: EventData;
}

export type RequestStatus = "running" | "completed" | "failed" | "blocked";

export interface RequestSummary {
  id: string;
  question: string;
  route: Route | null;
  status: RequestStatus;
  created_at: string;
  latency_ms: number;
  cost_usd: number;
  tokens: number;
  llm_calls: number;
  mock: boolean;
}

export interface AppConfig {
  live_available: boolean;
  default_mock: boolean;
  phoenix_url: string;
  supervisor_model: string;
  agent_model: string;
}

export interface Spend {
  spent_usd: number;
  budget_usd: number;
}

export const ROUTE_TO_NODE: Record<Route, AgentNode> = {
  sports: "stats_guru",
  movies: "cinema_buff",
  out_of_scope: "out_of_scope",
};

export const AGENTS: Record<AgentNode, { name: string; handles: string }> = {
  supervisor: { name: "Supervisor", handles: "Picks a route" },
  stats_guru: { name: "Stats Guru", handles: "IPL · SQLite" },
  cinema_buff: { name: "Cinema Buff", handles: "Movies · Wikipedia" },
  out_of_scope: { name: "Out of scope", handles: "Polite decline" },
};
