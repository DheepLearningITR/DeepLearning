import { useEffect, useState } from "react";
import { Play } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { listRequests } from "../lib/api";
import { fmtCost, fmtSeconds, fmtTime, fmtTokens } from "../lib/format";
import { AGENTS, ROUTE_TO_NODE, type RequestStatus, type RequestSummary } from "../lib/types";

const STATUS: Record<RequestStatus, { word: string; cls: string }> = {
  completed: { word: "Completed", cls: "text-board" },
  running: { word: "Running", cls: "text-lamp-ink" },
  failed: { word: "Failed", cls: "text-stamp" },
  blocked: { word: "Budget blocked", cls: "text-stamp" },
};

export function History() {
  const [rows, setRows] = useState<RequestSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    listRequests().then(setRows, (e: Error) => setError(e.message));
  }, []);

  const open = (id: string) => navigate(`/?replay=${id}`);

  return (
    <main className="mx-auto max-w-[96rem] px-6 py-6">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="board-label text-[1.8rem] tracking-[0.06em] text-ink">History</h1>
        <p className="text-[1rem] text-ink-2">Pick a request to replay its route on the board.</p>
      </div>

      <div className="overflow-x-auto bg-surface shadow-[0_2px_10px_-4px_rgb(10_30_20/0.25)]">
        <table className="w-full min-w-[56rem] border-collapse text-left">
          <thead className="bg-board text-paint-dim">
            <tr className="board-label text-[0.85rem]">
              <th scope="col" className="px-5 py-3 font-semibold">Time</th>
              <th scope="col" className="px-3 py-3 font-semibold">Question</th>
              <th scope="col" className="px-3 py-3 font-semibold">Route</th>
              <th scope="col" className="px-3 py-3 text-right font-semibold">Calls</th>
              <th scope="col" className="px-3 py-3 text-right font-semibold">Tokens</th>
              <th scope="col" className="px-3 py-3 text-right font-semibold">Cost $</th>
              <th scope="col" className="px-3 py-3 text-right font-semibold">Time s</th>
              <th scope="col" className="px-3 py-3 font-semibold">Status</th>
              <th scope="col" className="px-5 py-3"><span className="sr-only">Replay</span></th>
            </tr>
          </thead>
          <tbody>
            {rows?.map((r) => {
              const node = r.route ? ROUTE_TO_NODE[r.route] : null;
              return (
                <tr
                  key={r.id}
                  onClick={() => open(r.id)}
                  className="group cursor-pointer border-b border-rule text-[1.02rem] transition-colors hover:bg-lamp/15"
                >
                  <td className="whitespace-nowrap px-5 py-3.5 font-board text-[1.1rem] tabular-nums text-ink-2">
                    {fmtTime(r.created_at)}
                  </td>
                  <td className="max-w-[34rem] px-3 py-3.5 text-ink">
                    {r.question}
                    {r.mock && (
                      <span className="board-label ml-2 whitespace-nowrap border border-ink-3 px-1.5 py-px align-middle text-[0.75rem] text-ink-2">
                        Mock
                      </span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-3.5">
                    {node ? (
                      node === "out_of_scope" ? (
                        <span className="board-label bg-stamp px-1.5 py-0.5 text-[0.95rem] text-paint">Out of scope</span>
                      ) : (
                        <span className="board-label text-[1rem] text-ink">{AGENTS[node].name}</span>
                      )
                    ) : (
                      <span className="text-ink-3">—</span>
                    )}
                  </td>
                  <td className="px-3 py-3.5 text-right font-board text-[1.1rem] tabular-nums">{r.llm_calls}</td>
                  <td className="px-3 py-3.5 text-right font-board text-[1.1rem] tabular-nums">{fmtTokens(r.tokens)}</td>
                  <td className="px-3 py-3.5 text-right font-board text-[1.1rem] tabular-nums">{fmtCost(r.cost_usd)}</td>
                  <td className="px-3 py-3.5 text-right font-board text-[1.1rem] tabular-nums">{fmtSeconds(r.latency_ms)}</td>
                  <td className={`board-label whitespace-nowrap px-3 py-3.5 text-[0.95rem] ${STATUS[r.status].cls}`}>
                    {STATUS[r.status].word}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        open(r.id);
                      }}
                      className="board-label inline-flex items-center gap-1.5 text-[0.9rem] text-board opacity-70 group-hover:opacity-100 focus-visible:opacity-100"
                    >
                      <Play aria-hidden className="size-4" />
                      Replay
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {rows && rows.length === 0 && (
          <p className="px-5 py-10 text-center text-[1.05rem] text-ink-2">
            No requests yet. Ask a question and it will appear here.
          </p>
        )}
        {!rows && !error && <p className="px-5 py-10 text-center text-[1.05rem] text-ink-3">Loading history…</p>}
        {error && (
          <p className="px-5 py-10 text-center text-[1.05rem] text-stamp">
            Couldn't load history: {error} Check that the API is running.
          </p>
        )}
      </div>
    </main>
  );
}
