import { ExternalLink } from "lucide-react";
import { NavLink } from "react-router-dom";
import type { AppConfig, Spend } from "../lib/types";
import { NumberPlate } from "./NumberPlate";

const tab = ({ isActive }: { isActive: boolean }) =>
  `board-label relative px-1 py-1 text-[1.15rem] tracking-[0.08em] transition-colors ${
    isActive
      ? "text-paint after:absolute after:inset-x-0 after:-bottom-1.5 lg:after:-bottom-[0.95rem] after:h-1 after:bg-lamp"
      : "text-paint-dim hover:text-paint"
  }`;

interface Props {
  spend: Spend | null;
  config: AppConfig | null;
  mock: boolean;
  onMockChange: (mock: boolean) => void;
  busy: boolean;
}

/** Live / Mock: whether the model calls are real. The tools always run for real. */
function ModeSwitch({ config, mock, onMockChange, busy }: Omit<Props, "spend">) {
  const liveLocked = config != null && !config.live_available;
  const seg = (active: boolean) =>
    `board-label px-3 py-1 text-[0.95rem] tracking-[0.08em] transition-colors disabled:cursor-not-allowed ${
      active ? "bg-paint text-board" : "text-paint-dim hover:text-paint disabled:hover:text-paint-dim"
    }`;
  return (
    <div className="flex items-center gap-2">
      <span id="mode-label" className="board-label text-[0.8rem] text-paint-dim">
        Model
      </span>
      <div role="group" aria-labelledby="mode-label" className="flex border border-paint-dim">
        <button
          type="button"
          aria-pressed={!mock}
          disabled={liveLocked || busy}
          onClick={() => onMockChange(false)}
          title={liveLocked ? "Add OPENROUTER_API_KEY to the backend .env to enable live model calls." : "Real model calls through OpenRouter"}
          className={seg(!mock)}
        >
          Live
        </button>
        <button
          type="button"
          aria-pressed={mock}
          disabled={busy}
          onClick={() => onMockChange(true)}
          title="Scripted model replies for the six sample questions. SQL and Wikipedia still run for real; nothing is spent."
          className={seg(mock)}
        >
          Mock
        </button>
      </div>
      {liveLocked && <span className="text-[0.85rem] text-paint-dim">No API key</span>}
    </div>
  );
}

/** The green header strip: wordmark, tabs, model switch, today's spend as plates, Phoenix link. */
export function CostStrip({ spend, config, mock, onMockChange, busy }: Props) {
  const pct = spend ? Math.round((spend.spent_usd / spend.budget_usd) * 100) : 0;
  return (
    <header className="bg-board text-paint">
      <div className="mx-auto flex max-w-[96rem] flex-wrap items-center gap-x-10 gap-y-3 px-4 py-3.5 sm:px-6">
        <NavLink to="/" className="flex items-center gap-2.5" aria-label="FanDesk home">
          <span aria-hidden className="block size-4 rounded-full border-2 border-lamp-deep bg-lamp" />
          <span className="font-board text-[1.9rem] font-bold uppercase leading-none tracking-[0.04em]">FanDesk</span>
        </NavLink>

        <nav aria-label="Main" className="flex gap-7">
          <NavLink to="/" end className={tab}>
            Ask
          </NavLink>
          <NavLink to="/history" className={tab}>
            History
          </NavLink>
        </nav>

        <div className="ml-auto flex flex-wrap items-center gap-x-7 gap-y-2">
          <ModeSwitch config={config} mock={mock} onMockChange={onMockChange} busy={busy} />
          <div className="flex items-center gap-3">
            <span className="board-label text-right text-[0.8rem] leading-tight text-paint-dim">
              Spent
              <br />
              today
            </span>
            <NumberPlate label="Spent today in dollars" slots={5} size="lg" value={spend ? spend.spent_usd.toFixed(3) : null} />
            <span className="board-label text-[0.95rem] text-paint-dim">
              of ${spend ? spend.budget_usd.toFixed(2) : "—"}
              <span className="ml-2 text-paint">{pct}%</span>
            </span>
          </div>
          <a
            href={config?.phoenix_url ?? "http://localhost:6006"}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-[0.95rem] font-semibold text-paint underline decoration-board-line underline-offset-4 hover:decoration-paint"
          >
            Phoenix traces
            <ExternalLink aria-hidden className="size-4" />
          </a>
        </div>
      </div>
    </header>
  );
}
