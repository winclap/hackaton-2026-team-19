import { useState, useCallback, useRef, useEffect } from "react";
import { startReport, pollReport } from "./api";
import type { ReportData, BriefItem, ClusterItem, JobPoll } from "./api";

/* ── Types ─────────────────────────────────────────────── */

type Phase =
  | { name: "landing"; error?: string }
  | { name: "loading"; jobId: string; status: JobPoll["status"]; message: string }
  | { name: "done"; data: ReportData };

/* ── Header ────────────────────────────────────────────── */

function Header({ onLogoClick }: { onLogoClick: () => void }) {
  return (
    <header
      style={{ background: "var(--black)" }}
      className="sticky top-0 z-50 h-[60px] px-8 flex items-center justify-between"
    >
      <button
        onClick={onLogoClick}
        className="flex items-center gap-2.5 cursor-pointer"
      >
        <span
          style={{ background: "var(--accent)" }}
          className="w-2 h-2 rounded-full inline-block"
        />
        <span className="text-white font-extrabold text-[1.05rem] tracking-tight">
          The Real Voice Brief
        </span>
      </button>
      <span
        style={{ color: "#a78bfa", borderColor: "#4c1d95" }}
        className="text-[0.7rem] border rounded-full px-2.5 py-0.5 font-bold tracking-widest"
      >
        by Winclap
      </span>
    </header>
  );
}

/* ── Hero + Search Card ────────────────────────────────── */

function HeroSection({
  onAnalyze,
  error,
}: {
  onAnalyze: (appName: string, country: string) => void;
  error?: string;
}) {
  const [appName, setAppName] = useState("");
  const [country, setCountry] = useState("us");

  function submit() {
    const trimmed = appName.trim();
    if (!trimmed) return;
    onAnalyze(trimmed, country);
  }

  return (
    <>
      {/* Hero */}
      <div
        style={{ background: "var(--black)" }}
        className="text-white text-center px-8 pt-16 pb-20"
      >
        <h1 className="text-[clamp(1.8rem,4vw,2.8rem)] font-extrabold tracking-tight leading-[1.1] mb-4">
          Scrape{" "}
          <span style={{ color: "#a78bfa" }} className="font-normal text-[0.65em] align-middle mx-1.5">
            →
          </span>{" "}
          Brief{" "}
          <span style={{ color: "#a78bfa" }} className="font-normal text-[0.65em] align-middle mx-1.5">
            →
          </span>{" "}
          Scale
        </h1>
        <p style={{ color: "#9ca3af" }} className="text-base max-w-[520px] mx-auto mb-10 leading-7">
          Analizamos{" "}
          <strong style={{ color: "#e5e7eb", fontWeight: 600 }}>
            lo que dicen los usuarios reales
          </strong>{" "}
          en todas las plataformas y lo combinamos con{" "}
          <strong style={{ color: "#e5e7eb", fontWeight: 600 }}>
            la performance histórica de tus creativos
          </strong>{" "}
          para generarte briefs listos para ejecutar y escalar.
        </p>
      </div>

      {/* Search card floating over hero */}
      <div className="max-w-[680px] mx-auto px-4 -mt-10 relative z-10">
        <div
          style={{ boxShadow: "0 8px 40px rgba(0,0,0,.18)" }}
          className="bg-white rounded-[var(--radius)] p-7"
        >
          <div className="flex gap-3 items-end flex-wrap">
            {/* App name */}
            <div className="flex flex-col gap-1.5 flex-1 min-w-[200px]">
              <label
                style={{ color: "var(--gray-600)" }}
                className="text-[0.78rem] font-semibold uppercase tracking-[0.5px]"
              >
                Nombre de la app
              </label>
              <input
                type="text"
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
                placeholder="Ej: DiDi, Rappi, Ualá..."
                style={{
                  border: "1.5px solid var(--gray-200)",
                  background: "var(--gray-50)",
                  color: "var(--gray-800)",
                }}
                className="rounded-lg px-3.5 py-2.5 text-[0.95rem] outline-none transition-all focus:border-[var(--accent)] focus:bg-white"
              />
            </div>

            {/* Country */}
            <div className="flex flex-col gap-1.5">
              <label
                style={{ color: "var(--gray-600)" }}
                className="text-[0.78rem] font-semibold uppercase tracking-[0.5px]"
              >
                País
              </label>
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                style={{
                  border: "1.5px solid var(--gray-200)",
                  background: "var(--gray-50)",
                  color: "var(--gray-800)",
                }}
                className="rounded-lg px-3.5 py-2.5 text-[0.95rem] outline-none focus:border-[var(--accent)]"
              >
                <option value="ar">🇦🇷 Argentina</option>
                <option value="mx">🇲🇽 México</option>
                <option value="br">🇧🇷 Brasil</option>
                <option value="co">🇨🇴 Colombia</option>
                <option value="cl">🇨🇱 Chile</option>
                <option value="us">🇺🇸 Estados Unidos</option>
              </select>
            </div>

            {/* Analyze button */}
            <button
              onClick={submit}
              style={{ background: "var(--accent)" }}
              className="text-white rounded-lg px-6 py-2.5 text-[0.95rem] font-bold cursor-pointer transition-opacity hover:opacity-90 active:scale-95 flex items-center gap-2 h-[42px] whitespace-nowrap"
            >
              <span>⚡</span> Analizar
            </button>
          </div>

          {error && (
            <div
              style={{ background: "var(--red-bg)", color: "var(--red)", border: "1.5px solid #fca5a5" }}
              className="mt-4 rounded-[var(--radius)] px-4 py-3 text-sm"
            >
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>

      {/* Empty state */}
      <div className="text-center py-16" style={{ color: "var(--gray-400)" }}>
        <div className="text-5xl mb-3">🔍</div>
        <p className="text-base">Ingresá el nombre de una app para comenzar el análisis.</p>
      </div>
    </>
  );
}

/* ── Loading View ──────────────────────────────────────── */

const STEPS: { icon: string; label: string; statuses: JobPoll["status"][] }[] = [
  {
    icon: "📱",
    label: "Scrapeando App Store y Google Play",
    statuses: ["queued", "scraping"],
  },
  {
    icon: "💬",
    label: "Recolectando menciones en Reddit",
    statuses: ["scraping"],
  },
  {
    icon: "🧠",
    label: "Analizando con AI",
    statuses: ["quick_analysis", "deep_analysis"],
  },
  {
    icon: "🎯",
    label: "Generando creative briefs",
    statuses: ["deep_analysis"],
  },
];

function stepState(
  stepIdx: number,
  currentStatus: JobPoll["status"],
): "pending" | "active" | "done" {
  const order: JobPoll["status"][] = [
    "queued",
    "scraping",
    "quick_analysis",
    "deep_analysis",
    "done",
  ];
  const currentIdx = order.indexOf(currentStatus);

  if (currentStatus === "done") return "done";

  if (STEPS[stepIdx].statuses.includes(currentStatus)) return "active";

  // Determine step's earliest status
  const firstStatus = STEPS[stepIdx].statuses[0];
  const firstIdx = order.indexOf(firstStatus);
  if (currentIdx > firstIdx) return "done";

  return "pending";
}

function LoadingView({
  status,
  message,
}: {
  status: JobPoll["status"];
  message: string;
}) {
  return (
    <>
      {/* Hero (no search interaction during loading) */}
      <div style={{ background: "var(--black)" }} className="text-white text-center px-8 pt-16 pb-20">
        <h1 className="text-[clamp(1.8rem,4vw,2.8rem)] font-extrabold tracking-tight leading-[1.1] mb-4">
          Scrape{" "}
          <span style={{ color: "#a78bfa" }} className="font-normal text-[0.65em] align-middle mx-1.5">→</span>{" "}
          Brief{" "}
          <span style={{ color: "#a78bfa" }} className="font-normal text-[0.65em] align-middle mx-1.5">→</span>{" "}
          Scale
        </h1>
      </div>

      <div className="max-w-[500px] mx-auto px-4 mt-12 text-center">
        <div className="spinner" />
        <p style={{ color: "var(--gray-600)" }} className="font-semibold mb-2">
          {message || "Analizando reviews..."}
        </p>
        <div className="flex flex-col gap-3 mt-6 text-left">
          {STEPS.map((step, i) => {
            const s = stepState(i, status);
            return (
              <div key={i} className={`step ${s === "active" ? "active" : s === "done" ? "done" : ""}`}>
                <span className="w-6 text-center text-lg">{s === "done" ? "✓" : step.icon}</span>
                {step.label}
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

/* ── Stat Card ─────────────────────────────────────────── */

function StatCard({
  value,
  label,
  color,
}: {
  value: string;
  label: string;
  color?: string;
}) {
  return (
    <div
      style={{ background: "white", boxShadow: "var(--shadow)", borderRadius: "var(--radius)" }}
      className="p-5 text-center"
    >
      <div
        className="text-[1.8rem] font-extrabold"
        style={{ color: color ?? "var(--gray-800)" }}
      >
        {value}
      </div>
      <div
        style={{ color: "var(--gray-400)" }}
        className="text-[0.78rem] uppercase tracking-[0.5px] mt-0.5"
      >
        {label}
      </div>
    </div>
  );
}

/* ── Brief Card ────────────────────────────────────────── */

function BriefCard({ brief }: { brief: BriefItem }) {
  const [open, setOpen] = useState(false);
  const funnelEmoji: Record<string, string> = {
    awareness: "📣",
    consideration: "🤔",
    activation: "⚡",
    usage: "🔄",
    retention: "🔁",
    conversion: "🎯",
  };

  return (
    <div
      data-open={open}
      className="brief-card"
      style={{
        background: "white",
        borderRadius: "var(--radius)",
        boxShadow: "var(--shadow)",
        marginBottom: "1rem",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        onClick={() => setOpen(!open)}
        style={{
          borderBottom: open ? "1.5px solid var(--gray-200)" : "1.5px solid transparent",
          cursor: "pointer",
        }}
        className="px-6 py-4 flex items-center gap-3 select-none transition-all"
      >
        <div
          style={{
            background: "var(--accent-light)",
            color: "var(--accent)",
            borderRadius: "8px",
            width: "32px",
            height: "32px",
          }}
          className="flex items-center justify-center font-extrabold text-[0.85rem] shrink-0"
        >
          {brief.brief_id}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-bold text-[0.95rem]" style={{ color: "var(--gray-800)" }}>
            {brief.title}
          </div>
          <div className="flex gap-2 mt-1 flex-wrap">
            <span
              style={{ background: "var(--accent-light)", color: "var(--accent)" }}
              className="text-[0.7rem] font-semibold px-2.5 py-0.5 rounded-full capitalize"
            >
              {funnelEmoji[brief.funnel_stage] ?? "🎯"} {brief.funnel_stage}
            </span>
            <span
              style={{ background: "#dbeafe", color: "#1d4ed8" }}
              className="text-[0.7rem] font-semibold px-2.5 py-0.5 rounded-full"
            >
              📐 {brief.format}
            </span>
            {brief.target_segment && (
              <span
                style={{ background: "#d1fae5", color: "#065f46" }}
                className="text-[0.7rem] font-semibold px-2.5 py-0.5 rounded-full"
              >
                👤 {brief.target_segment}
              </span>
            )}
          </div>
        </div>
        <span className="brief-chevron text-base">▼</span>
      </div>

      {/* Body */}
      <div className="brief-body px-6 py-5">
        {/* Hook */}
        <div
          style={{
            fontStyle: "italic",
            fontWeight: 800,
            fontSize: "1.2rem",
            color: "var(--gray-800)",
            borderBottom: "1px solid var(--gray-200)",
            paddingBottom: "1.2rem",
            marginBottom: "1.2rem",
          }}
        >
          "{brief.hook}"
        </div>

        {/* Grid: insight / script / angle / cta */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
          {[
            { label: "Insight", value: brief.insight },
            { label: "Concepto del script", value: brief.script_concept },
            { label: "Ángulo narrativo", value: brief.angle },
            { label: "Call to action", value: brief.cta },
          ].map(({ label, value }) => (
            <div key={label}>
              <label
                style={{ color: "var(--gray-400)" }}
                className="block text-[0.72rem] font-bold uppercase tracking-[0.5px] mb-1"
              >
                {label}
              </label>
              <p className="text-[0.88rem]" style={{ color: "var(--gray-800)", lineHeight: 1.5 }}>
                {value}
              </p>
            </div>
          ))}
        </div>

        {/* Testimonial */}
        <div
          style={{
            background: "var(--amber-bg)",
            borderLeft: "3px solid var(--amber)",
            borderRadius: "8px",
            fontStyle: "italic",
            fontSize: "0.88rem",
            marginBottom: "1rem",
          }}
          className="px-4 py-3 leading-relaxed"
        >
          "{brief.customer_quote_source}"
        </div>

        {/* Why this wins */}
        {brief.why_this_wins && (
          <div
            style={{
              background: "var(--accent-light)",
              borderLeft: "3px solid var(--accent)",
              borderRadius: "8px",
            }}
            className="px-4 py-3"
          >
            <label
              style={{ color: "var(--accent)" }}
              className="block text-[0.72rem] font-bold uppercase tracking-[0.5px] mb-1"
            >
              ⚡ Por qué este brief gana
            </label>
            <p className="text-[0.88rem]" style={{ color: "var(--gray-800)", lineHeight: 1.5 }}>
              {brief.why_this_wins}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Cluster Card ──────────────────────────────────────── */

function ClusterCard({ cluster }: { cluster: ClusterItem }) {
  const emotions = Object.keys(cluster.top_emotions ?? {}).slice(0, 4);

  return (
    <div
      style={{
        background: "white",
        borderRadius: "var(--radius)",
        boxShadow: "var(--shadow)",
      }}
      className="px-6 py-5 mb-3"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="font-bold text-[0.95rem] capitalize" style={{ color: "var(--gray-800)" }}>
          {(cluster.theme ?? "").replace(/_/g, " ")}
        </div>
        <span
          style={{ background: "var(--gray-100)", color: "var(--gray-400)" }}
          className="text-[0.78rem] font-semibold px-3 py-1 rounded-full"
        >
          {cluster.volume} reviews · {cluster.pct_of_total}%
        </span>
      </div>

      {emotions.length > 0 && (
        <div className="mb-3">
          <div
            style={{ color: "var(--gray-400)" }}
            className="text-[0.7rem] font-bold uppercase tracking-[0.5px] mb-1.5"
          >
            Emociones dominantes
          </div>
          <div className="flex flex-wrap gap-1.5">
            {emotions.map((e) => (
              <span
                key={e}
                style={{ background: "#fef3c7", color: "#92400e" }}
                className="text-[0.75rem] font-semibold px-2.5 py-0.5 rounded-full"
              >
                {e}
              </span>
            ))}
          </div>
        </div>
      )}

      {cluster.top_quotes?.length > 0 && (
        <div style={{ borderTop: "1px solid var(--gray-100)" }} className="pt-3 mt-1">
          {cluster.top_quotes.slice(0, 3).map((q, i) => (
            <div
              key={i}
              style={{
                background: "var(--gray-50)",
                color: "var(--gray-600)",
                fontStyle: "italic",
                fontSize: "0.8rem",
                borderRadius: "6px",
              }}
              className="px-3 py-1.5 mb-1.5 leading-relaxed"
            >
              "{q}"
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Results View ──────────────────────────────────────── */

type Tab = "briefs" | "insights" | "frases";

function ResultsView({
  data,
  onReset,
}: {
  data: ReportData;
  onReset: () => void;
}) {
  const [tab, setTab] = useState<Tab>("briefs");
  const sent = data.sentiment_summary?.sentiment_distribution ?? {};
  const total = data.total_reviews;

  const positivePct = total > 0 ? Math.round(((sent["positive"] ?? 0) / total) * 100) : 0;
  const neutralPct  = total > 0 ? Math.round(((sent["neutral"]  ?? 0) / total) * 100) : 0;
  const negativePct = total > 0 ? Math.round(((sent["negative"] ?? 0) / total) * 100) : 0;

  // Collect all verbatim quotes from clusters
  const allQuotes: string[] = [];
  for (const cluster of data.clusters ?? []) {
    for (const q of cluster.top_quotes ?? []) {
      if (q && !allQuotes.includes(q)) allQuotes.push(q);
      if (allQuotes.length >= 30) break;
    }
    if (allQuotes.length >= 30) break;
  }

  return (
    <div className="max-w-[960px] mx-auto px-6 py-12">
      {/* Results header */}
      <div className="flex justify-between items-start mb-8 flex-wrap gap-4">
        <div>
          <div className="text-[1.5rem] font-extrabold tracking-tight" style={{ color: "var(--gray-800)" }}>
            {data.brand_name}
          </div>
          <div style={{ color: "var(--gray-400)" }} className="text-[0.85rem] mt-1">
            {data.total_reviews} reviews analizadas · {data.briefs.length} briefs generados
          </div>
        </div>
        <button
          onClick={onReset}
          style={{ background: "var(--gray-100)", color: "var(--gray-600)" }}
          className="rounded-lg px-4 py-2 text-[0.85rem] font-semibold cursor-pointer hover:bg-[var(--gray-200)] transition-colors"
        >
          ← Nueva búsqueda
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-8">
        <StatCard value={String(data.total_reviews)} label="Reviews analizadas" />
        <StatCard value={`${positivePct}%`} label="Positivo" color="var(--green)" />
        <StatCard value={`${neutralPct}%`} label="Neutro" color="var(--amber)" />
        <StatCard value={`${negativePct}%`} label="Negativo" color="var(--red)" />
        <StatCard value={String(data.briefs.length)} label="Briefs generados" color="var(--accent)" />
      </div>

      {/* Tabs */}
      <div
        style={{ background: "var(--gray-100)", borderRadius: "10px" }}
        className="flex gap-1 p-1 mb-8"
      >
        {(["briefs", "insights", "frases"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: tab === t ? "white" : "transparent",
              color: tab === t ? "var(--gray-800)" : "var(--gray-600)",
              boxShadow: tab === t ? "0 1px 4px rgba(0,0,0,.1)" : "none",
            }}
            className="flex-1 text-center px-4 py-2 rounded-[7px] text-[0.88rem] font-semibold cursor-pointer transition-all"
          >
            {t === "briefs" ? "🎯 Creative Briefs" : t === "insights" ? "💡 Insights" : "💬 Frases clave"}
          </button>
        ))}
      </div>

      {/* Tab: Briefs */}
      {tab === "briefs" && (
        <div>
          {data.briefs.map((b) => (
            <BriefCard key={b.brief_id} brief={b} />
          ))}
        </div>
      )}

      {/* Tab: Insights (clusters) */}
      {tab === "insights" && (
        <div>
          <p style={{ color: "var(--gray-600)" }} className="text-[0.9rem] mb-5">
            Temas principales agrupados por cluster. Cada uno muestra volumen, emociones dominantes y las mejores quotes.
          </p>
          {data.clusters.length > 0 ? (
            data.clusters.map((c) => <ClusterCard key={c.theme} cluster={c} />)
          ) : (
            <p style={{ color: "var(--gray-400)" }} className="text-[0.9rem]">
              No hay clusters disponibles.
            </p>
          )}
        </div>
      )}

      {/* Tab: Frases */}
      {tab === "frases" && (
        <div>
          <p style={{ color: "var(--gray-600)" }} className="text-[0.9rem] mb-4">
            Frases textuales de usuarios reales que pueden usarse como hooks, testimoniales o inspiración para copy.
          </p>
          {allQuotes.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {allQuotes.map((q, i) => (
                <div
                  key={i}
                  style={{
                    background: "var(--amber-bg)",
                    borderLeft: "3px solid var(--amber)",
                    borderRadius: "8px",
                    fontStyle: "italic",
                    color: "var(--gray-800)",
                    fontSize: "0.88rem",
                  }}
                  className="px-4 py-3 leading-relaxed"
                >
                  "{q}"
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--gray-400)" }} className="text-[0.9rem]">
              No hay frases quotables disponibles.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

/* ── App (state machine) ───────────────────────────────── */

export default function App() {
  const [phase, setPhase] = useState<Phase>({ name: "landing" });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const handleAnalyze = useCallback(
    async (appName: string, country: string) => {
      try {
        const jobId = await startReport(appName, country);
        setPhase({ name: "loading", jobId, status: "queued", message: "Iniciando análisis..." });

        pollRef.current = setInterval(async () => {
          try {
            const poll = await pollReport(jobId);

            if (poll.status === "done" && poll.data) {
              stopPolling();
              setPhase({ name: "done", data: poll.data });
            } else if (poll.status === "error") {
              stopPolling();
              setPhase({ name: "landing", error: poll.error ?? "Error en el análisis" });
            } else {
              setPhase((prev) =>
                prev.name === "loading"
                  ? { ...prev, status: poll.status, message: messageForStatus(poll.status) }
                  : prev,
              );
            }
          } catch {
            // Keep polling on transient errors
          }
        }, 2500);
      } catch (e) {
        setPhase({
          name: "landing",
          error: e instanceof Error ? e.message : "No se pudo conectar con el servidor",
        });
      }
    },
    [stopPolling],
  );

  const handleReset = useCallback(() => {
    stopPolling();
    setPhase({ name: "landing" });
  }, [stopPolling]);

  return (
    <div className="min-h-screen" style={{ background: "var(--gray-50)" }}>
      <Header onLogoClick={handleReset} />

      {phase.name === "landing" && (
        <HeroSection onAnalyze={handleAnalyze} error={phase.error} />
      )}

      {phase.name === "loading" && (
        <LoadingView status={phase.status} message={phase.message} />
      )}

      {phase.name === "done" && (
        <ResultsView data={phase.data} onReset={handleReset} />
      )}
    </div>
  );
}

/* ── Helpers ───────────────────────────────────────────── */

function messageForStatus(status: JobPoll["status"]): string {
  switch (status) {
    case "queued":       return "En cola...";
    case "scraping":     return "Recolectando reviews...";
    case "quick_analysis": return "Analizando sentimiento y temas...";
    case "deep_analysis":  return "Analizando en profundidad con AI...";
    case "done":           return "¡Listo!";
    case "error":          return "Error";
    default:               return "Procesando...";
  }
}
