// src/components/charts/RiskDonutChart.tsx
// SVG donut chart — reads pre-aggregated risk counts from the backend.

import type { UserSummary } from "../../hooks/useUserSummary";

interface RiskDonutChartProps {
  summary: UserSummary;
}

// SVG circle circumference for r=16 ≈ 100.5 used as "100%" unit
const C = 100.5;

const SEGMENTS = [
  { key: "risk_high" as const,     label: "High Risk",  color: "#ef4444" },
  { key: "risk_medium" as const,   label: "Medium",     color: "#f59e0b" },
  { key: "risk_low" as const,      label: "Low Risk",   color: "#135bec" },
  { key: "risk_unscanned" as const,label: "Unscanned",  color: "#475569" },
];

export default function RiskDonutChart({ summary }: RiskDonutChartProps) {
  const total = summary.total_scanned;

  if (total === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex items-center justify-center text-slate-500 text-sm" style={{ minHeight: 180 }}>
        No scan data yet
      </div>
    );
  }

  let offset = 0;
  const arcs = SEGMENTS
    .map((seg) => {
      const count = summary[seg.key];
      const pct = (count / total) * C;
      const arc = { ...seg, count, pct, offset };
      offset += pct;
      return arc;
    })
    .filter((a) => a.count > 0);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2 mb-5">
        <span className="material-symbols-outlined text-primary text-base">donut_large</span>
        Risk Distribution
      </h3>

      <div className="flex items-center gap-6">
        {/* Donut */}
        <div className="relative shrink-0 w-28 h-28">
          <svg viewBox="0 0 36 36" className="w-full h-full" style={{ transform: "rotate(-90deg)" }}>
            <circle cx="18" cy="18" r="16" fill="transparent" stroke="#1e293b" strokeWidth="4" />
            {arcs.map((arc) => (
              <circle
                key={arc.key}
                cx="18" cy="18" r="16"
                fill="transparent"
                stroke={arc.color}
                strokeWidth="4"
                strokeDasharray={`${arc.pct.toFixed(2)} ${C}`}
                strokeDashoffset={`-${arc.offset.toFixed(2)}`}
              />
            ))}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-sm font-bold text-white">{total.toLocaleString()}</span>
            <span className="text-[9px] uppercase text-slate-400 tracking-wide">Total</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-2.5">
          {arcs.map((arc) => (
            <div key={arc.key} className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: arc.color }} />
                {arc.label}
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-slate-200">{arc.count.toLocaleString()}</span>
                <span className="text-[10px] text-slate-500">
                  ({((arc.count / total) * 100).toFixed(0)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
