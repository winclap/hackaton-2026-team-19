import { StrictMode, useState, useCallback } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import LandingPage from "./pages/LandingPage";
import LoadingPage from "./pages/LoadingPage";
import Dashboard from "./pages/Dashboard";
import { fetchAnalysis } from "./data/useData";
import type { DashboardData } from "./data/types";

type AppState =
  | { phase: "landing"; error?: string }
  | { phase: "loading"; brand: string }
  | { phase: "dashboard"; data: DashboardData };

function App() {
  const [state, setState] = useState<AppState>({ phase: "landing" });

  const handleAnalyze = useCallback(async (brand: string) => {
    setState({ phase: "loading", brand });
    try {
      const data = await fetchAnalysis(brand);
      setState({ phase: "dashboard", data });
    } catch (e) {
      setState({
        phase: "landing",
        error: e instanceof Error ? e.message : "Error desconocido",
      });
    }
  }, []);

  const handleReset = useCallback(() => {
    setState({ phase: "landing" });
  }, []);

  switch (state.phase) {
    case "landing":
      return <LandingPage onAnalyze={handleAnalyze} error={state.error} />;
    case "loading":
      return <LoadingPage brand={state.brand} />;
    case "dashboard":
      return <Dashboard data={state.data} onReset={handleReset} />;
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
