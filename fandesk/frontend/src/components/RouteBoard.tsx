import type { ReactNode } from "react";
import { History as HistoryIcon } from "lucide-react";
import type { NodeState, NodeStats, RunView } from "../lib/derive";
import { fmtCost, fmtSeconds } from "../lib/format";
import { AGENTS, type AgentNode, type FanEvent } from "../lib/types";
import { Lamp } from "./Lamp";
import { NumberPlate } from "./NumberPlate";

const SPECIALISTS: AgentNode[] = ["stats_guru", "cinema_buff", "out_of_scope"];

const STATUS_WORD: Record<NodeState, string> = {
  idle: "Waiting",
  live: "Working",
  done: "Done",
  skipped: "Not used",
};

// Fixed board columns: rail · lamp · agent · status · calls · tokens · cost · time.
// When the board is narrow, status moves under the name and plates sit in a 2×2 grid.
const WIDE = "@[45rem]:grid-cols-[1.75rem_1.75rem_minmax(8.5rem,1fr)_4.75rem_auto_auto_auto_auto]";
const GRID = `grid grid-cols-[1.75rem_1.75rem_minmax(0,1fr)] items-start gap-x-2.5 ${WIDE}`;
// Extra gutter between plate columns so they read as separate figures from a distance.
const GUTTER = "@[45rem]:ml-5";

// Vertical position of the lamp's centre inside a row (py-3 + lamp offset + half lamp).
const LAMP_Y = "1.725rem";

function PlateSlot({ label, children }: { label: string; children: ReactNode }) {
  return (
    <span className="flex flex-col gap-1 @[45rem]:contents">
      <span className="board-label text-[0.75rem] text-paint-dim @[45rem]:hidden">{label}</span>
      {children}
    </span>
  );
}

interface PlateValues {
  calls: string | null;
  tokens: string | null;
  cost: string | null;
  time: string | null;
}

type Wrap = (key: keyof PlateValues, node: ReactNode) => ReactNode;

function Plates({ v, hideWhenNarrow, wrap }: { v: PlateValues; hideWhenNarrow?: boolean; wrap?: Wrap }) {
  const w: Wrap = wrap ?? ((_, n) => n);
  return (
    <div
      className={`col-start-3 mt-3 w-fit grid-cols-[auto_auto] gap-x-3 gap-y-2 @[45rem]:contents ${hideWhenNarrow ? "hidden" : "grid"}`}
    >
      <PlateSlot label="Calls">{w("calls", <NumberPlate label="LLM calls" slots={1} value={v.calls} />)}</PlateSlot>
      <PlateSlot label="Tokens">
        {w("tokens", <NumberPlate label="Tokens" slots={5} value={v.tokens} className={GUTTER} />)}
      </PlateSlot>
      <PlateSlot label="Cost $">
        {w("cost", <NumberPlate label="Cost in dollars" slots={6} value={v.cost} className={GUTTER} />)}
      </PlateSlot>
      <PlateSlot label="Time s">
        {w("time", <NumberPlate label="Seconds" slots={4} value={v.time} className={GUTTER} />)}
      </PlateSlot>
    </div>
  );
}

const statsValues = (s: NodeStats, showZero: boolean): PlateValues => {
  const has = s.calls > 0 || (showZero && s.state === "done");
  return {
    calls: has ? String(s.calls) : null,
    tokens: has ? String(s.tokens) : null,
    cost: has ? fmtCost(s.cost) : null,
    time: s.ms != null ? fmtSeconds(s.ms) : null,
  };
};

/** The routing rail beside a row: trunk above and below the lamp, and a stub into it. */
function Rail({ up, down, stub, last }: { up: boolean; down: boolean; stub: boolean; last?: boolean }) {
  const c = (on: boolean) => (on ? "bg-lamp" : "bg-board-line");
  return (
    <span aria-hidden className="pointer-events-none absolute inset-y-0 left-0 w-7">
      <span className={`absolute left-1/2 top-0 w-[3px] -translate-x-1/2 ${c(up)}`} style={{ height: LAMP_Y }} />
      {!last && (
        <span className={`absolute bottom-0 left-1/2 w-[3px] -translate-x-1/2 ${c(down)}`} style={{ top: LAMP_Y }} />
      )}
      <span
        className={`absolute left-1/2 h-[3px] w-[calc(50%+0.625rem)] -translate-y-1/2 ${c(stub)}`}
        style={{ top: LAMP_Y }}
      />
    </span>
  );
}

function Status({ state, word, stamp }: { state: NodeState; word: string; stamp?: boolean }) {
  if (stamp) {
    return <span className="board-label whitespace-nowrap bg-stamp px-1.5 py-0.5 text-[0.95rem] text-paint">{word}</span>;
  }
  const tone = state === "live" ? "text-lamp" : state === "done" ? "text-paint" : "text-paint-dim";
  return <span className={`board-label whitespace-nowrap text-[1rem] ${tone}`}>{word}</span>;
}

function AgentRow(props: {
  name: string;
  handles: string;
  state: NodeState;
  status: ReactNode;
  plates: PlateValues;
  showPlatesNarrow: boolean;
  rail: { up: boolean; down: boolean; stub: boolean; last?: boolean };
}) {
  const quiet = props.state === "skipped";
  return (
    <div className={`${GRID} relative border-t border-board-line py-3`}>
      <Rail {...props.rail} />
      <span />
      <span className="mt-[0.35rem]">
        <Lamp state={props.state} />
      </span>
      <div>
        <div className={`board-label whitespace-nowrap text-[1.45rem] leading-tight ${quiet ? "text-paint-dim" : ""}`}>
          {props.name}
        </div>
        <div className="text-[0.9rem] text-paint-dim">
          {props.handles}
          <span className="ml-3 @[45rem]:hidden">{props.status}</span>
        </div>
      </div>
      <span className="mt-1 hidden @[45rem]:block">{props.status}</span>
      <Plates v={props.plates} hideWhenNarrow={!props.showPlatesNarrow} />
    </div>
  );
}

interface Props {
  run: RunView;
  events: FanEvent[];
  replaying: boolean;
  onJump: (seq: number) => void;
}

export function RouteBoard({ run, events, replaying, onJump }: Props) {
  const chosenIndex = run.chosen ? SPECIALISTS.indexOf(run.chosen) : -1;
  const routed = chosenIndex >= 0;
  const sup = run.nodes.supervisor;
  const supWord = sup.state === "live" ? "Deciding" : sup.state === "done" ? "Routed" : "Waiting";

  // Total row: each plate jumps to the event behind it.
  const llm = events.filter((e) => e.type === "llm.call");
  const priciest = llm.reduce<FanEvent | undefined>((a, e) => (!a || e.data.cost > a.data.cost ? e : a), undefined);
  const completed = events.find((e) => e.type === "request.completed");
  const totalTarget: Record<keyof PlateValues, FanEvent | undefined> = {
    calls: llm[0],
    tokens: llm[0],
    cost: priciest,
    time: completed,
  };
  const totals: PlateValues = run.totals
    ? {
        calls: String(run.totals.calls),
        tokens: String(run.totals.tokens),
        cost: fmtCost(run.totals.cost),
        time: fmtSeconds(run.totals.latency_ms),
      }
    : { calls: null, tokens: null, cost: null, time: null };

  const wrapTotal: Wrap = (k, node) => {
    const target = totalTarget[k];
    if (!run.totals || !target) return node;
    return (
      <button
        type="button"
        onClick={() => onJump(target.seq)}
        title="Show the event behind this number"
        className="flex self-start outline-offset-4 transition-transform hover:-translate-y-0.5"
      >
        {node}
      </button>
    );
  };

  return (
    <section
      aria-labelledby="board-title"
      className="@container border-[6px] border-board-deep bg-board text-paint shadow-[0_6px_18px_-8px_rgb(10_30_20/0.55)]"
    >
      <div className="border-b-2 border-board-line px-4 pb-3 pt-3.5 @[40rem]:px-6">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4">
          <h2 id="board-title" className="board-label text-[1.35rem] tracking-[0.08em]">
            Route board
          </h2>
          <p className="board-label inline-flex items-center gap-1.5 text-[0.85rem] text-paint-dim" aria-live="polite">
            {replaying && <HistoryIcon aria-hidden className="size-4 text-lamp" />}
            {replaying && <span className="text-lamp">Replay ·</span>}
            {run.status === "idle" && "Ask a question to start"}
            {run.status === "running" && <span className="text-lamp">Live</span>}
            {run.status === "done" && "Innings complete"}
            {run.status === "failed" && <span className="bg-stamp px-1.5 text-paint">Stopped: failed</span>}
            {run.status === "blocked" && <span className="bg-stamp px-1.5 text-paint">Stopped: budget</span>}
          </p>
        </div>
        {run.question && (
          <p className="row-in mt-1.5 text-[1.3rem] font-medium leading-snug text-paint">“{run.question}”</p>
        )}
      </div>

      <div className="px-4 pb-4 pt-3 @[40rem]:px-6">
        {/* Column heads, painted once; columns never move. */}
        <div className={`${GRID} board-label hidden pb-2 text-[0.8rem] text-paint-dim @[45rem]:grid`}>
          <span />
          <span />
          <span>Agent</span>
          <span>Status</span>
          <span className="text-center">Calls</span>
          <span className={`text-center ${GUTTER}`}>Tokens</span>
          <span className={`text-center ${GUTTER}`}>Cost $</span>
          <span className={`text-center ${GUTTER}`}>Time s</span>
        </div>

        <AgentRow
          name={AGENTS.supervisor.name}
          handles={AGENTS.supervisor.handles}
          state={sup.state}
          status={<Status state={sup.state} word={supWord} />}
          plates={statsValues(sup, false)}
          showPlatesNarrow={sup.state !== "idle"}
          rail={{ up: false, down: routed, stub: sup.state !== "idle" }}
        />

        {run.reason && (
          <div className={`${GRID} row-in relative`}>
            <span aria-hidden className="pointer-events-none absolute inset-y-0 left-0 w-7">
              <span className={`absolute inset-y-0 left-1/2 w-[3px] -translate-x-1/2 ${routed ? "bg-lamp" : "bg-board-line"}`} />
            </span>
            <span />
            <span />
            <p className="col-start-3 mb-3 max-w-[60ch] text-[1.05rem] leading-snug text-paint @[45rem]:col-span-6">
              <span className="board-label mr-2 text-[0.85rem] text-lamp">Why</span>
              {run.reason}
            </p>
          </div>
        )}

        {/* Specialists: the trunk is lit down to the chosen row only. */}
        {SPECIALISTS.map((id, i) => {
          const n = run.nodes[id];
          const declined = id === "out_of_scope" && n.state === "done";
          return (
            <AgentRow
              key={id}
              name={AGENTS[id].name}
              handles={AGENTS[id].handles}
              state={n.state}
              status={<Status state={n.state} word={declined ? "Declined" : STATUS_WORD[n.state]} stamp={declined} />}
              plates={statsValues(n, id === "out_of_scope")}
              showPlatesNarrow={n.state === "live" || (n.state === "done" && !declined)}
              rail={{ up: chosenIndex >= i, down: chosenIndex > i, stub: i === chosenIndex, last: i === SPECIALISTS.length - 1 }}
            />
          );
        })}

        {/* Total row, under a painted double rule, in the same plate columns. */}
        <div className={`${GRID} border-t-[5px] border-double border-paint-dim pt-3`}>
          <span />
          <span />
          <div className="board-label mt-1 text-[1.45rem] leading-tight">Total</div>
          <span className="hidden @[45rem]:block" />
          <Plates v={totals} wrap={wrapTotal} />
        </div>
      </div>
    </section>
  );
}
