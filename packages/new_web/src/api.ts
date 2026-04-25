/**
 * API client for packages/api FastAPI server.
 *
 * POST /api/report  → {job_id, status}
 * GET  /api/report/{id} → JobPoll
 */

export interface BriefItem {
  brief_id: number;
  title: string;
  hook: string;
  insight: string;
  customer_quote_source: string;
  angle: string;
  format: string;
  funnel_stage: string;
  target_segment: string;
  script_concept: string;
  cta: string;
  why_this_wins: string;
}

export interface ClusterItem {
  theme: string;
  volume: number;
  pct_of_total: number;
  top_emotions: Record<string, number>;
  top_quotes: string[];
}

export interface SentimentSummary {
  total_reviews: number;
  sentiment_distribution: Record<string, number>;
  avg_compound: number;
}

export interface ReportData {
  brand_name: string;
  total_reviews: number;
  timestamp: string;
  stats: { clusters: number; briefs: number };
  sentiment_summary: SentimentSummary;
  clusters: ClusterItem[];
  briefs: BriefItem[];
}

export interface JobPoll {
  job_id: string;
  status: "queued" | "scraping" | "quick_analysis" | "deep_analysis" | "done" | "error";
  brand: string;
  total_reviews: number;
  data?: ReportData;
  error?: string;
  quick_result?: object;
}

export async function startReport(
  appName: string,
  country: string,
): Promise<string> {
  const res = await fetch("/api/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      brand: {
        name: appName,
        category: "",
        audience: "",
        nonnegotiables: [],
      },
      sources: [
        {
          source: "appstore",
          query: appName,
          country,
          max_reviews: 500,
        },
      ],
      webhook_url: null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? `Error ${res.status}`);
  }
  const json = await res.json() as { job_id: string };
  return json.job_id;
}

export async function pollReport(jobId: string): Promise<JobPoll> {
  const res = await fetch(`/api/report/${jobId}`);
  if (!res.ok) {
    throw new Error(`Poll error ${res.status}`);
  }
  return res.json() as Promise<JobPoll>;
}
