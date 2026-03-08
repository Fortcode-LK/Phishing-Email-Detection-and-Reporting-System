// src/components/charts/DomainBarChart.tsx
// Horizontal stacked bar chart for top sender domains (admin view).
// Legitimate = green, Phishing = red. Bars scale relative to max domain total.

import type { TopSenderDomain } from "../../hooks/useAdminMetrics";

interface DomainBarChartProps {
  domains: TopSenderDomain[];
}

export default function DomainBarChart({ domains }: DomainBarChartProps) {
  if (domains.length === 0) return null;

  const maxCount = Math.max(1, ...domains.map((d) => d.count));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800 flex items-center gap-2">
        <span className="material-symbols-outlined text-primary text-base">bar_chart</span>
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
          Sender Volume
        </h3>
        <span className="text-[10px] text-slate-500 ml-auto">
          top {domains.length} domains
        </span>
      </div>

      {/* Bars */}
      <div className="p-5 space-y-4">
        {domains.map((d) => {
          const legitCount = d.count - d.phishing_count;
          const legitPct = (legitCount / maxCount) * 100;
          const phishPct = (d.phishing_count / maxCount) * 100;
          const phishingRate = d.count > 0 ? d.phishing_count / d.count : 0;

          const rateColor =
            phishingRate >= 0.6
              ? "text-red-400"
              : phishingRate >= 0.25
              ? "text-amber-400"
              : "text-emerald-400";

          return (
            <div key={d.domain}>
              {/* Label row */}
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-mono text-slate-300 truncate max-w-[200px]">
                  {d.domain}
                </span>
                <div className="flex items-center gap-2 shrink-0 ml-2">
                  <span className="text-[10px] text-slate-500">
                    {d.count.toLocaleString()} emails
                  </span>
                  {d.phishing_count > 0 && (
                    <span className={`text-[10px] font-bold ${rateColor}`}>
                      {(phishingRate * 100).toFixed(0)}% phish
                    </span>
                  )}
                </div>
              </div>

              {/* Stacked bar */}
              <div className="flex h-2.5 rounded-full overflow-hidden bg-slate-800/80">
                {legitPct > 0 && (
                  <div
                    className="h-full bg-emerald-500/60 transition-all duration-500"
                    style={{ width: `${legitPct}%` }}
                  />
                )}
                {phishPct > 0 && (
                  <div
                    className="h-full bg-red-500/70 transition-all duration-500"
                    style={{ width: `${phishPct}%` }}
                  />
                )}
              </div>
            </div>
          );
        })}

        {/* Legend */}
        <div className="flex items-center gap-5 pt-2 border-t border-slate-800">
          <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500/60 inline-block" />
            Legitimate
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-2 h-2 rounded-full bg-red-500/70 inline-block" />
            Phishing
          </span>
        </div>
      </div>
    </div>
  );
}
