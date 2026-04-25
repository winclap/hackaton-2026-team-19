export default function LoadingPage({ brand }: { brand: string }) {
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="text-center space-y-6">
        {/* Spinner */}
        <div className="inline-block w-10 h-10 border-[3px] border-gray-200 border-t-primary rounded-full animate-spin" />
        <div className="space-y-2">
          <p className="text-base text-gray-800">
            Analyzing{" "}
            <span className="font-semibold text-gray-900">{brand}</span>
          </p>
          <p className="text-sm text-gray-400 max-w-xs mx-auto leading-relaxed">
            Clustering reviews, extracting insights, and generating creative
            briefs with Claude...
          </p>
        </div>
      </div>
    </div>
  );
}
