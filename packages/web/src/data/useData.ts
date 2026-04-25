import type { DashboardData } from "./types";
import mockData from "./mock.json";

export async function fetchAnalysis(_brand: string): Promise<DashboardData> {
  // Simulate network delay, then return pre-analyzed mock data
  await new Promise((r) => setTimeout(r, 1200));
  return mockData as unknown as DashboardData;
}

export function downloadJSON(data: DashboardData) {
  const { raw_analyses: _, ...clean } = data;
  const blob = new Blob([JSON.stringify(clean, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${data.brand_name.toLowerCase()}_voice_report.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadCSV(data: DashboardData) {
  if (!data.raw_analyses.length) return;
  const keys = Object.keys(data.raw_analyses[0]);
  const header = keys.join(",");
  const rows = data.raw_analyses.map((r) =>
    keys
      .map((k) => {
        const v = r[k];
        const s = v == null ? "" : String(v);
        return s.includes(",") || s.includes('"') || s.includes("\n")
          ? `"${s.replace(/"/g, '""')}"`
          : s;
      })
      .join(",")
  );
  const csv = [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${data.brand_name.toLowerCase()}_reviews.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
