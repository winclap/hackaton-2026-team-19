import type { DashboardData, ClusterItem, BriefItem } from "../data/types";
import { downloadJSON, downloadCSV } from "../data/useData";

/* ── helpers ─────────────────────────────────────────────── */

function fmtRuntime(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return m > 0 ? `${m} min ${sec} sec` : `${sec} sec`;
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* ── Stats Strip ─────────────────────────────────────────── */

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-card rounded-xl p-5 shadow-sm">
      <div className="text-2xl font-bold text-gray-900 tracking-tight">
        {value}
      </div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

function StatsStrip({ data }: { data: DashboardData }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <StatCard
        value={data.total_reviews.toLocaleString()}
        label="Reviews analyzed"
      />
      <StatCard
        value={String(data.stats.clusters)}
        label="Theme clusters"
      />
      <StatCard
        value={String(data.stats.briefs)}
        label="Creative briefs"
      />
      <StatCard
        value={`$${data.stats.api_cost_usd.toFixed(2)}`}
        label="API cost"
      />
      <StatCard
        value={fmtRuntime(data.stats.runtime_seconds)}
        label="Runtime"
      />
    </div>
  );
}

/* ── Cluster Card ────────────────────────────────────────── */

function ClusterCard({ cluster }: { cluster: ClusterItem }) {
  return (
    <div className="bg-card rounded-xl p-6 shadow-sm border-l-4 border-l-primary hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-900">{cluster.theme}</h3>
        <span className="text-xs text-gray-400 shrink-0 ml-3">
          {cluster.volume.toLocaleString()} reviews &middot;{" "}
          {cluster.percentage}%
        </span>
      </div>

      {/* Emotion pills */}
      <div className="flex gap-1.5 mb-4">
        {cluster.top_emotions.map((e) => (
          <span
            key={e}
            className="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-500"
          >
            {e}
          </span>
        ))}
      </div>

      {/* Featured quote */}
      <div className="relative mb-3">
        <span className="absolute -left-1 -top-3 text-4xl text-accent/30 font-serif leading-none select-none">
          &ldquo;
        </span>
        <p className="text-base italic text-gray-700 leading-relaxed pl-5">
          {cluster.featured_quote}
          <span className="text-accent/30 font-serif">&rdquo;</span>
        </p>
      </div>

      {/* Moment */}
      <p className="text-xs text-gray-400">
        <span className="font-medium text-gray-500">Moment:</span>{" "}
        {cluster.top_moment}
      </p>
    </div>
  );
}

/* ── Brief Card ──────────────────────────────────────────── */

function BriefCard({ brief }: { brief: BriefItem }) {
  return (
    <div className="bg-card rounded-xl p-6 shadow-sm border-l-4 border-l-accent">
      {/* Title */}
      <h3 className="text-xl font-bold text-gray-900 mb-3">
        <span className="text-accent font-mono text-base mr-2">
          #{brief.brief_id}
        </span>
        {brief.title}
      </h3>

      {/* Hook */}
      <div className="relative mb-4">
        <span className="absolute -left-1 -top-3 text-5xl text-accent/25 font-serif leading-none select-none">
          &ldquo;
        </span>
        <p className="text-xl italic text-accent font-medium leading-snug pl-6">
          {brief.hook}
          <span className="text-accent/25 font-serif">&rdquo;</span>
        </p>
      </div>

      {/* Source */}
      <p className="text-xs text-gray-400 mb-4">
        Source: &ldquo;{brief.customer_quote_source}&rdquo;
      </p>

      {/* Meta pills */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-600 font-medium">
          {brief.format}
        </span>
        <span className="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-600 font-medium">
          {brief.angle}
        </span>
        <span className="text-xs px-3 py-1 rounded-full bg-primary/10 text-primary font-medium">
          {brief.funnel_stage}
        </span>
      </div>

      {/* Target */}
      <p className="text-xs text-gray-400 mb-3">
        <span className="font-medium text-gray-500">Target:</span>{" "}
        {brief.target_segment}
      </p>

      {/* Script concept */}
      <p className="text-sm text-gray-600 leading-relaxed mb-4">
        {brief.script_concept}
      </p>

      {/* CTA */}
      <div className="bg-accent/8 rounded-lg px-4 py-2.5 mb-3">
        <span className="text-xs text-gray-400 uppercase tracking-wider">
          CTA:
        </span>{" "}
        <span className="text-sm font-semibold text-accent">{brief.cta}</span>
      </div>

      {/* Why this wins */}
      <p className="text-xs italic text-gray-400">{brief.why_this_wins}</p>
    </div>
  );
}

/* ── Dashboard (main) ────────────────────────────────────── */

export default function Dashboard({
  data,
  onReset,
}: {
  data: DashboardData;
  onReset: () => void;
}) {
  return (
    <div className="min-h-screen bg-surface">
      <div className="max-w-[1040px] mx-auto px-6 py-16">
        {/* ── HEADER ──────────────────────────────────── */}
        <header className="mb-24">
          <button
            onClick={onReset}
            className="text-xs text-gray-400 hover:text-primary transition mb-6 block cursor-pointer"
          >
            &larr; New analysis
          </button>
          <p className="text-xs font-medium tracking-widest uppercase text-primary mb-3">
            Winclap Voice Agent
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight mb-3">
            Voice Intelligence Report
          </h1>
          <p className="text-lg text-gray-500 mb-4">
            {data.brand_name} &mdash; auto-generated from{" "}
            {data.total_reviews.toLocaleString()} real customer reviews
          </p>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-300" />
              Reddit
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-300" />
              App Store
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-300" />
              Trustpilot
            </span>
            <span className="ml-auto">
              Last refresh: {fmtDate(data.timestamp)}
            </span>
          </div>
        </header>

        {/* ── STATS STRIP ─────────────────────────────── */}
        <section className="mb-24">
          <StatsStrip data={data} />
        </section>

        {/* ── WHAT THEY'RE SAYING ─────────────────────── */}
        <section className="mb-24">
          <p className="text-xs font-medium tracking-widest uppercase text-primary mb-2">
            Cluster Analysis
          </p>
          <h2 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">
            What They&apos;re Saying
          </h2>
          <p className="text-sm text-gray-400 mb-8">
            {data.stats.clusters} theme clusters extracted from{" "}
            {data.total_reviews.toLocaleString()} reviews, ranked by volume.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.clusters.map((c) => (
              <ClusterCard key={c.theme} cluster={c} />
            ))}
          </div>
        </section>

        {/* ── CREATIVE BRIEFS ─────────────────────────── */}
        <section className="mb-24">
          <p className="text-xs font-medium tracking-widest uppercase text-accent mb-2">
            Creative Strategy
          </p>
          <h2 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">
            {data.stats.briefs} Creative Briefs
          </h2>
          <p className="text-sm text-gray-400 mb-8">
            Each brief is grounded in a real customer quote. Ready for Meta,
            TikTok, and YouTube.
          </p>
          <div className="space-y-6">
            {data.briefs.map((b) => (
              <BriefCard key={b.brief_id} brief={b} />
            ))}
          </div>
        </section>

        {/* ── FOOTER ──────────────────────────────────── */}
        <footer className="border-t border-gray-200 pt-8 pb-16 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-400">
            Generated by Winclap Voice Agent &middot; {fmtDate(data.timestamp)}
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => downloadJSON(data)}
              className="text-xs text-gray-400 hover:text-primary border border-gray-200 rounded-lg px-3 py-1.5 transition cursor-pointer hover:border-primary/30"
            >
              Download JSON
            </button>
            <button
              onClick={() => downloadCSV(data)}
              className="text-xs text-gray-400 hover:text-primary border border-gray-200 rounded-lg px-3 py-1.5 transition cursor-pointer hover:border-primary/30"
            >
              Download CSV
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
