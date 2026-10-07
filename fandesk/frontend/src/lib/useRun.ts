import { useCallback, useMemo, useRef, useState } from "react";
import { ask, getRequestEvents } from "./api";
import { deriveRun } from "./derive";
import type { FanEvent } from "./types";

const MAX_REPLAY_GAP_MS = 1500;

/** Owns one request's event list, whether it is streaming live or replaying. */
export function useRun(onFinished?: () => void) {
  const [events, setEvents] = useState<FanEvent[]>([]);
  const [replaying, setReplaying] = useState(false);
  const controller = useRef<AbortController | null>(null);

  const reset = () => {
    controller.current?.abort();
    controller.current = new AbortController();
    setEvents([]);
    return controller.current.signal;
  };

  const start = useCallback(
    async (question: string, mock: boolean) => {
      const signal = reset();
      setReplaying(false);
      try {
        await ask(question, mock, (e) => setEvents((prev) => [...prev, e]), signal);
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setEvents((prev) => [
          ...prev,
          {
            request_id: prev[0]?.request_id ?? "local",
            seq: prev.length,
            ts: new Date().toISOString(),
            type: "request.failed",
            node: "response",
            data: { message: (err as Error).message },
          },
        ]);
      }
      onFinished?.();
    },
    [onFinished],
  );

  /** Re-plays saved events with their original spacing (long gaps capped). */
  const replay = useCallback(async (id: string) => {
    const signal = reset();
    setReplaying(true);
    const saved = await getRequestEvents(id);
    for (let i = 0; i < saved.length; i++) {
      if (signal.aborted) return;
      const gap = i === 0 ? 0 : Date.parse(saved[i].ts) - Date.parse(saved[i - 1].ts);
      await new Promise((r) => setTimeout(r, Math.min(gap, MAX_REPLAY_GAP_MS)));
      if (signal.aborted) return;
      setEvents((prev) => [...prev, saved[i]]);
    }
  }, []);

  const run = useMemo(() => deriveRun(events), [events]);
  return { events, run, replaying, start, replay };
}
