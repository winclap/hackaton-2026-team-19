export interface DashboardData {
  brand_name: string;
  total_reviews: number;
  timestamp: string;
  stats: {
    clusters: number;
    briefs: number;
    api_cost_usd: number;
    runtime_seconds: number;
  };
  clusters: ClusterItem[];
  briefs: BriefItem[];
  raw_analyses: RawReview[];
}

export interface ClusterItem {
  theme: string;
  volume: number;
  percentage: number;
  top_emotions: string[];
  top_moment: string;
  featured_quote: string;
}

export interface BriefItem {
  brief_id: number;
  title: string;
  hook: string;
  customer_quote_source: string;
  angle: string;
  format: string;
  funnel_stage: string;
  target_segment: string;
  script_concept: string;
  cta: string;
  why_this_wins: string;
}

export interface RawReview {
  dataType: string;
  username: string;
  title: string | null;
  body: string;
  theme: string;
  sentiment: string;
  emotion: string;
  funnel_stage: string;
  creative_potential: number;
  verbatim_quote: string | null;
  [key: string]: unknown;
}
