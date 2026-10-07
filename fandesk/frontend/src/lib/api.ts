import { mockAsk, mockGetRequest, mockListRequests, mockSpend } from "./mock";
import type { AppConfig, FanEvent, RequestSummary, Spend } from "./types";

/**
 * Design-preview only: play scripted streams in the browser with no backend.
 * Normal use talks to the FastAPI backend, whose own Live/Mock switch scripts
 * only the model while the SQL and Wikipedia tools run for real.
 */
export const OFFLINE_PREVIEW = import.meta.env.VITE_USE_MOCK_STREAM === "true";

/** POST /api/ask and read the SSE stream with fetch (EventSource can't POST). */
async function askLive(question: string, mock: boolean, onEvent: (e: FanEvent) => void, signal?: AbortSignal) {
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ question, mock }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`The API answered ${res.status}. Is the backend running?`);

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    let cut: number;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      const data = frame
        .split("\n")
        .filter((l) => l.startsWith("data:"))
        .map((l) => l.slice(5).trimStart())
        .join("\n");
      if (data) onEvent(JSON.parse(data));
    }
  }
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`The API answered ${res.status}.`);
  return res.json();
}

export const ask = (question: string, mock: boolean, onEvent: (e: FanEvent) => void, signal?: AbortSignal) =>
  OFFLINE_PREVIEW ? mockAsk(question, onEvent, signal) : askLive(question, mock, onEvent, signal);

export const listRequests = (): Promise<RequestSummary[]> =>
  OFFLINE_PREVIEW ? mockListRequests() : getJson("/api/requests");

export const getRequestEvents = async (id: string): Promise<FanEvent[]> =>
  OFFLINE_PREVIEW ? mockGetRequest(id) : (await getJson<{ events: FanEvent[] }>(`/api/requests/${id}`)).events;

export const getSpend = (): Promise<Spend> => (OFFLINE_PREVIEW ? mockSpend() : getJson("/api/spend"));

const PREVIEW_CONFIG: AppConfig = {
  live_available: false,
  default_mock: true,
  phoenix_url: "http://localhost:6006",
  supervisor_model: "mock",
  agent_model: "mock",
};

export const getConfig = (): Promise<AppConfig> =>
  OFFLINE_PREVIEW ? Promise.resolve(PREVIEW_CONFIG) : getJson("/api/config");

export const phoenixTraceUrl = (phoenixUrl: string, requestId: string) =>
  `${phoenixUrl}/redirects/traces/${requestId}`;
