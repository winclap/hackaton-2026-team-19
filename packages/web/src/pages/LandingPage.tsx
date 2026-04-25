import { useState } from "react";

export default function LandingPage({
  onAnalyze,
  error,
}: {
  onAnalyze: (brand: string) => void;
  error?: string;
}) {
  const [brand, setBrand] = useState("");

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="w-full max-w-md px-6 space-y-8 text-center">
        <div className="space-y-3">
          <p className="text-xs font-medium tracking-widest uppercase text-primary">
            Winclap
          </p>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
            Voice Intelligence
          </h1>
          <p className="text-gray-500 text-sm leading-relaxed">
            Analyze real customer reviews and generate creative advertising
            insights powered by AI.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (brand.trim()) onAnalyze(brand.trim());
          }}
          className="space-y-3"
        >
          <input
            type="text"
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder="Brand or app name..."
            autoFocus
            className="w-full bg-card border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition shadow-sm"
          />
          <button
            type="submit"
            disabled={!brand.trim()}
            className="w-full py-3 rounded-xl bg-primary text-white font-semibold text-sm hover:opacity-90 disabled:opacity-30 disabled:cursor-default transition cursor-pointer shadow-sm"
          >
            Analyze Reviews
          </button>
        </form>

        {error && (
          <p className="text-sm text-red-500 bg-red-50 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <p className="text-xs text-gray-400">
          Powered by Claude &middot; Winclap Growth Intelligence
        </p>
      </div>
    </div>
  );
}
