import { useState, type FormEvent } from "react";
import { ArrowRight, LoaderCircle } from "lucide-react";
import { SAMPLE_QUESTIONS } from "../lib/mock";

interface Props {
  busy: boolean;
  /** Once a run is on screen the chips shrink to one scrollable line. */
  compact?: boolean;
  onAsk: (question: string) => void;
}

export function QuestionBar({ busy, compact = false, onAsk }: Props) {
  const [q, setQ] = useState("");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const question = q.trim();
    if (question && !busy) onAsk(question);
  };

  const pick = (question: string) => {
    setQ(question);
    if (!busy) onAsk(question);
  };

  return (
    <div>
      <form onSubmit={submit} className="flex gap-3">
        <label htmlFor="question" className="sr-only">
          Ask about IPL cricket or movies
        </label>
        <input
          id="question"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ask about IPL cricket or movies…"
          autoComplete="off"
          className="min-w-0 flex-1 border border-rule bg-surface px-3 py-3 sm:px-4 text-[1.2rem] text-ink placeholder:text-ink-3 focus:border-board focus:outline-none focus-visible:outline-3 focus-visible:outline-lamp"
        />
        <button
          type="submit"
          disabled={busy || !q.trim()}
          className="board-label inline-flex shrink-0 items-center gap-2 bg-lamp px-4 text-[1.25rem] sm:px-6 tracking-[0.08em] text-plate-ink shadow-[0_2px_4px_rgb(0_0_0/0.2)] transition-colors hover:bg-lamp-hover active:translate-y-px disabled:cursor-not-allowed disabled:bg-rule disabled:text-ink-3 disabled:shadow-none"
        >
          {busy ? (
            <>
              <LoaderCircle aria-hidden className="size-5 animate-spin motion-reduce:animate-none" />
              Scoring
            </>
          ) : (
            <>
              Ask
              <ArrowRight aria-hidden className="hidden size-5 sm:block" />
            </>
          )}
        </button>
      </form>

      <div className={`flex flex-wrap items-center ${compact ? "mt-2.5 gap-1.5" : "mt-3 gap-2"}`}>
        <span className="board-label mr-1 text-[0.85rem] text-ink-2">Try</span>
        {SAMPLE_QUESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            disabled={busy}
            onClick={() => pick(s)}
            className={`border border-rule bg-surface text-ink-2 transition-colors hover:border-board hover:text-board disabled:cursor-not-allowed disabled:opacity-50 ${compact ? "px-2.5 py-1 text-[0.85rem]" : "px-3 py-1.5 text-[0.95rem]"}`}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
