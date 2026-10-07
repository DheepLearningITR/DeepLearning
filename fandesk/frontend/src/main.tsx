import { StrictMode, useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { CostStrip } from "./components/CostStrip";
import { getConfig, getSpend } from "./lib/api";
import type { AppConfig, Spend } from "./lib/types";
import { Ask } from "./pages/Ask";
import { History } from "./pages/History";
import "./index.css";

function App() {
  const [spend, setSpend] = useState<Spend | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [mock, setMock] = useState(true);
  const [busy, setBusy] = useState(false);

  const refreshSpend = useCallback(() => {
    getSpend().then(setSpend, () => setSpend(null));
  }, []);
  useEffect(refreshSpend, [refreshSpend]);

  useEffect(() => {
    getConfig().then(
      (c) => {
        setConfig(c);
        setMock(c.default_mock || !c.live_available);
      },
      () => setConfig(null),
    );
  }, []);

  return (
    <BrowserRouter>
      <CostStrip spend={spend} config={config} mock={mock} onMockChange={setMock} busy={busy} />
      <Routes>
        <Route
          path="/"
          element={<Ask mock={mock} config={config} onBusyChange={setBusy} onSpendChange={refreshSpend} />}
        />
        <Route path="/history" element={<History />} />
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
