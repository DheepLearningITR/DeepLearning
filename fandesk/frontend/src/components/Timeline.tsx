import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowRightLeft,
  Ban,
  BookOpen,
  ChevronDown,
  CircleCheck,
  Database,
  Flag,
  MessageSquareText,
  Play,
  Search,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { fmtCost, fmtSeconds, fmtTokens } from "../lib/format";
import { AGENTS, type AgentNode, type FanEvent } from "../lib/types";

export interface TimelineItem {
  key: string;
  seq: number;
  icon: LucideIcon;
  title: string;
  agent?: AgentNode;
  note?: string;
  detail?: { kind: "sql" | "text"; body: string };
  ms?: number;
  tokens?: number;
  cost?: number;
  tone?: "stamp";
  pending?: boolean;
}

const TOOL_ICON: Record<string, LucideIcon> = {
  get_schema: Database,
  run_sql: Database,
  search_wikipedia: Search,
  get_page_summary: BookOpen,
};

/** Turns raw events into timeline rows; a tool call and its result share one row. */
export function toItems(events: FanEvent[]): TimelineItem[] {
  const items: TimelineItem[] = [];
  const openTool: Partial<Record<string, TimelineItem>> = {};

  for (const e of events) {
    const agent = (e.node in AGENTS ? e.node : undefined) as AgentNode | undefined;
    const base = { key: `e${e.seq}`, seq: e.seq, agent };
    switch (e.type) {
      case "request.received":
        items.push({ ...base, icon: MessageSquareText, title: "Question received", note: e.data.question });
        break;
      case "supervisor.decision":
        items.push({
          ...base,
          icon: ArrowRightLeft,
          title: `Routed to ${AGENTS[routeNode(e.data.route)].name}`,
          note: e.data.reason,
        });
        break;
      case "agent.start":
        items.push({ ...base, icon: Play, title: `${agent ? AGENTS[agent].name : "Agent"} started` });
        break;
      case "llm.call":
        items.push({
          ...base,
          icon: Sparkles,
          title: "LLM call",
          note: e.data.mock ? "Scripted reply (mock)" : shortModel(e.data.model),
          ms: e.data.ms,
          tokens: (e.data.prompt_tokens ?? 0) + (e.data.completion_tokens ?? 0),
          cost: e.data.cost,
        });
        break;
      case "tool.call": {
        const args = e.data.args ?? {};
        const item: TimelineItem = {
          ...base,
          icon: TOOL_ICON[e.data.name] ?? Database,
          title: e.data.name,
          note: args.query ?? args.title,
          detail: args.sql ? { kind: "sql", body: args.sql } : undefined,
          pending: true,
        };
        openTool[`${e.node}:${e.data.name}`] = item;
        items.push(item);
        break;
      }
      case "tool.result": {
        const item = openTool[`${e.node}:${e.data.name}`];
        if (item) {
          item.pending = false;
          item.ms = e.data.ms;
          item.note = item.note ? `${item.note} → ${e.data.summary}` : e.data.summary;
          delete openTool[`${e.node}:${e.data.name}`];
        }
        break;
      }
      case "agent.answer":
        items.push({ ...base, icon: Flag, title: "Answer ready" });
        break;
      case "request.completed":
        items.push({
          ...base,
          icon: CircleCheck,
          title: `Completed in ${fmtSeconds(e.data.latency_ms)} s`,
          note: `${e.data.llm_calls} LLM calls · ${fmtTokens(e.data.tokens)} tokens · $${fmtCost(e.data.total_cost)}`,
        });
        break;
      case "budget.blocked":
        items.push({ ...base, icon: Ban, title: "Stopped by the budget guard", note: e.data.message, tone: "stamp" });
        break;
      case "request.failed":
        items.push({ ...base, icon: AlertTriangle, title: "Request failed", note: e.data.message, tone: "stamp" });
        break;
    }
  }
  return items;
}

const routeNode = (route: string): AgentNode =>
  route === "sports" ? "stats_guru" : route === "movies" ? "cinema_buff" : "out_of_scope";

const shortModel = (model?: string) => (model ? model.split("/").pop() : "");

function Row({ item, index, maxMs, highlighted }: { item: TimelineItem; index: number; maxMs: number; highlighted: boolean }) {
  const [open, setOpen] = useState(false);
  const Icon = item.icon;
  const pct = item.ms != null && maxMs > 0 ? Math.max(1.5, (item.ms / maxMs) * 100) : 0;
  const isTool = item.icon !== Sparkles && item.ms != null;

  return (
    <li
      id={`event-${item.seq}`}
      className={`row-in grid grid-cols-[2rem_1.5rem_minmax(0,1fr)] gap-x-3 border-b border-rule px-5 py-3 transition-colors duration-500 ${
        highlighted ? "bg-lamp/25" : ""
      }`}
    >
      <span className="pt-0.5 text-right font-board text-[1.05rem] font-semibold tabular-nums text-ink-3">
        {index}
      </span>
      <Icon
        aria-hidden
        className={`mt-1 size-5 ${item.tone === "stamp" ? "text-stamp" : "text-board"}`}
        strokeWidth={2}
      />
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
          <span
            className={`text-[1.05rem] font-semibold ${item.tone === "stamp" ? "text-stamp" : "text-ink"} ${
              item.detail || item.title.includes("_") ? "font-mono text-[0.95rem]" : ""
            }`}
          >
            {item.title}
          </span>
          {item.agent && item.agent !== "out_of_scope" && (
            <span className="board-label text-[0.8rem] text-ink-3">{AGENTS[item.agent].name}</span>
          )}
          {item.pending && <span className="board-label text-[0.8rem] text-lamp-ink">Running</span>}
        </div>
        {item.note && <p className="mt-0.5 text-[0.95rem] leading-snug text-ink-2">{item.note}</p>}

        {item.ms != null && (
          <div className="mt-2 flex items-center gap-3">
            {/* Bar length is the step's real duration against the slowest step. */}
            <span className="relative h-2 flex-1 bg-ground">
              <span
                className={`absolute inset-y-0 left-0 transition-[width] duration-500 ${isTool ? "bg-board" : "bg-lamp"}`}
                style={{ width: `${pct}%` }}
              />
            </span>
            <span className="w-28 text-right font-board text-[0.95rem] font-medium tabular-nums text-ink-2">
              {item.ms.toLocaleString("en-US")} ms
            </span>
          </div>
        )}
        {item.tokens != null && (
          <p className="mt-1 font-board text-[0.95rem] font-medium tabular-nums text-ink-3">
            {fmtTokens(item.tokens)} tokens · ${fmtCost(item.cost ?? 0, 6)}
          </p>
        )}

        {item.detail && (
          <div className="mt-2">
            <button
              type="button"
              onClick={() => setOpen((o) => !o)}
              aria-expanded={open}
              className="inline-flex items-center gap-1 text-[0.9rem] font-semibold text-board underline decoration-rule hover:decoration-board"
            >
              <ChevronDown aria-hidden className={`size-4 transition-transform ${open ? "rotate-180" : ""}`} />
              {open ? "Hide query" : "Show query"}
            </button>
            {open && (
              <pre className="mt-2 overflow-x-auto bg-board-deep px-4 py-3 font-mono text-[0.85rem] leading-relaxed text-paint">
                {item.detail.body}
              </pre>
            )}
          </div>
        )}
      </div>
    </li>
  );
}

export function Timeline({ events, highlight }: { events: FanEvent[]; highlight: number | null }) {
  const items = toItems(events);
  const maxMs = Math.max(0, ...items.map((i) => i.ms ?? 0));
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    if (highlight == null) return;
    document.getElementById(`event-${highlight}`)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [highlight]);

  useEffect(() => {
    const el = listRef.current;
    if (el && highlight == null) el.scrollTop = el.scrollHeight;
  }, [items.length, highlight]);

  return (
    <section aria-labelledby="timeline-title" className="flex min-h-0 flex-col bg-surface shadow-[0_2px_10px_-4px_rgb(10_30_20/0.25)]">
      <div className="flex items-baseline justify-between border-b border-rule px-5 pb-3 pt-4">
        <h2 id="timeline-title" className="board-label text-[1.35rem] tracking-[0.08em] text-ink">
          Ball by ball
        </h2>
        <span className="board-label text-[0.85rem] text-ink-3">{items.length} events</span>
      </div>
      {items.length === 0 ? (
        <p className="px-5 py-8 text-[1rem] leading-relaxed text-ink-2">
          Every step shows up here as it happens: the routing decision, each LLM call with its tokens and cost, and
          every SQL query or Wikipedia lookup.
        </p>
      ) : (
        <ol ref={listRef} className="min-h-0 flex-1 overflow-y-auto" aria-live="polite">
          {items.map((it, i) => (
            <Row key={it.key} item={it} index={i + 1} maxMs={maxMs} highlighted={highlight === it.seq} />
          ))}
        </ol>
      )}
    </section>
  );
}
