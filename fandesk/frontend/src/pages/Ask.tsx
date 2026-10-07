import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AnswerCard } from "../components/AnswerCard";
import { QuestionBar } from "../components/QuestionBar";
import { RouteBoard } from "../components/RouteBoard";
import { Timeline } from "../components/Timeline";
import type { AppConfig } from "../lib/types";
import { useRun } from "../lib/useRun";

interface Props {
  mock: boolean;
  config: AppConfig | null;
  onBusyChange: (busy: boolean) => void;
  onSpendChange: () => void;
}

export function Ask({ mock, config, onBusyChange, onSpendChange }: Props) {
  const { events, run, replaying, start, replay } = useRun(onSpendChange);
  const [highlight, setHighlight] = useState<number | null>(null);
  const [params, setParams] = useSearchParams();
  const replayId = params.get("replay");
  const started = useRef<string | null>(null);
  const answerRef = useRef<HTMLElement>(null);
  const presenterScrolled = useRef(false);

  useEffect(() => {
    if (replayId && started.current !== replayId) {
      started.current = replayId;
      replay(replayId);
    }
  }, [replayId, replay]);

  useEffect(() => onBusyChange(run.status === "running"), [run.status, onBusyChange]);

  // While a run plays, note if the presenter scrolls; otherwise bring the answer into view at the end.
  useEffect(() => {
    if (run.status !== "running") return;
    presenterScrolled.current = false;
    const mark = () => (presenterScrolled.current = true);
    window.addEventListener("wheel", mark, { passive: true });
    window.addEventListener("touchmove", mark, { passive: true });
    window.addEventListener("keydown", mark);
    return () => {
      window.removeEventListener("wheel", mark);
      window.removeEventListener("touchmove", mark);
      window.removeEventListener("keydown", mark);
    };
  }, [run.status]);

  useEffect(() => {
    if ((run.status === "done" || run.status === "failed" || run.status === "blocked") && !presenterScrolled.current) {
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      answerRef.current?.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" });
    }
  }, [run.status]);

  const ask = (q: string) => {
    setHighlight(null);
    if (replayId) setParams({}, { replace: true });
    start(q, mock);
  };

  const jump = (seq: number) => {
    setHighlight(seq);
    window.setTimeout(() => setHighlight((h) => (h === seq ? null : h)), 2400);
  };

  return (
    <main className="mx-auto grid max-w-[96rem] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(22rem,26rem)]">
      <div className="flex min-w-0 flex-col gap-6">
        <QuestionBar busy={run.status === "running"} compact={run.status !== "idle"} onAsk={ask} />
        <RouteBoard run={run} events={events} replaying={replaying} onJump={jump} />
        <AnswerCard ref={answerRef} run={run} phoenixUrl={config?.phoenix_url} />
      </div>

      <div className="lg:sticky lg:top-6 lg:h-[calc(100dvh-8.5rem)] lg:self-start">
        <Timeline events={events} highlight={highlight} />
      </div>
    </main>
  );
}
