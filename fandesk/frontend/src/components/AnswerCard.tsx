import { ExternalLink } from "lucide-react";
import { forwardRef } from "react";
import { OFFLINE_PREVIEW, phoenixTraceUrl } from "../lib/api";
import type { RunView } from "../lib/derive";
import { AGENTS } from "../lib/types";

/** Models sometimes slip into Markdown; show **bold** as bold rather than raw asterisks. */
const withBold = (text: string) =>
  text.split(/\*\*(.+?)\*\*/g).map((part, i) => (i % 2 ? <strong key={i} className="font-semibold">{part}</strong> : part));

const wikiUrl = (title: string) => `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g, "_"))}`;

export const AnswerCard = forwardRef<HTMLElement, { run: RunView; phoenixUrl?: string }>(function AnswerCard({ run, phoenixUrl }, ref) {
  const traceUrl = !OFFLINE_PREVIEW && phoenixUrl && run.requestId ? phoenixTraceUrl(phoenixUrl, run.requestId) : null;
  if (run.status === "failed" || run.status === "blocked") {
    return (
      <section ref={ref} className="row-in border-2 border-stamp bg-surface px-6 py-5">
        <h2 className="board-label text-[1.2rem] text-stamp">
          {run.status === "blocked" ? "Stopped by the budget guard" : "This request failed"}
        </h2>
        <p className="mt-1 text-[1.05rem] text-ink">{run.error}</p>
        <p className="mt-1 text-[0.95rem] text-ink-2">
          {run.status === "blocked"
            ? "Raise DAILY_BUDGET_USD in .env or wait until tomorrow, then ask again."
            : "Check the timeline for the last step that ran, then ask again."}
        </p>
      </section>
    );
  }
  if (!run.answer) return null;

  const agent = run.chosen ?? "out_of_scope";
  const isWiki = agent === "cinema_buff";

  return (
    <section ref={ref} aria-labelledby="answer-title" className="row-in scroll-mt-6 bg-surface px-6 pb-5 pt-4 shadow-[0_2px_10px_-4px_rgb(10_30_20/0.25)]">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="answer-title" className="board-label text-[1.35rem] tracking-[0.08em] text-ink">
          Answer <span className="whitespace-nowrap text-ink-3">from {AGENTS[agent].name}</span>
        </h2>
        {run.mock && (
          <span className="board-label border border-ink-3 px-2 py-0.5 text-[0.8rem] text-ink-2">Mock answer</span>
        )}
      </div>
      <p className="mt-3 max-w-[68ch] whitespace-pre-line text-[1.2rem] leading-relaxed text-ink">{withBold(run.answer)}</p>

      {((run.sources && run.sources.length > 0) || traceUrl) && (
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 text-[0.95rem] text-ink-2">
          {run.sources && run.sources.length > 0 && (
            <>
              <span className="board-label text-[0.85rem] text-ink-3">Sources</span>
              {run.sources.map((s) =>
                isWiki ? (
                  <a
                    key={s}
                    href={wikiUrl(s)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-medium text-board underline decoration-rule hover:decoration-board"
                  >
                    {s}
                    <ExternalLink aria-hidden className="size-3.5" />
                  </a>
                ) : (
                  <span key={s} className="font-mono text-[0.9rem]">
                    {s}
                  </span>
                ),
              )}
            </>
          )}
          {traceUrl && (
            <a
              href={traceUrl}
              target="_blank"
              rel="noreferrer"
              className="ml-auto inline-flex items-center gap-1.5 font-semibold text-board underline decoration-rule hover:decoration-board"
            >
              View trace in Phoenix
              <ExternalLink aria-hidden className="size-4" />
            </a>
          )}
        </div>
      )}
    </section>
  );
});
