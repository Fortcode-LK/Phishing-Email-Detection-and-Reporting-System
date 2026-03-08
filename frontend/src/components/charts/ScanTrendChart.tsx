// src/components/charts/ScanTrendChart.tsx
// SVG area chart — receives pre-aggregated daily data from the backend.
// No client-side bucketing or hardcoded date ranges.

import type { DailyTrendPoint } from "../../hooks/useUserSummary";

interface ScanTrendChartProps {
  trend: DailyTrendPoint[];
}

export default function ScanTrendChart({ trend }: ScanTrendChartProps) {
  if (trend.length === 0) return null;

  const maxCount = Math.max(1, ...trend.map((b) => b.total));

  // SVG layout
  const W = 400, H = 120;
  const MT = 8, MB = 4, ML = 8, MR = 8;
  const PW = W - ML - MR;
  const PH = H - MT - MB;
  const n = trend.length;

  const xOf = (i: number) => ML + (i / Math.max(n - 1, 1)) * PW;
  const yOf = (count: number) => MT + (1 - count / maxCount) * PH;

  const buildLine = (vals: number[]) =>
    vals.map((v, i) => `${i === 0 ? "M" : "L"} ${xOf(i).toFixed(1)} ${yOf(v).toFixed(1)}`).join(" ");

  const buildArea = (vals: number[]) =>
    `${buildLine(vals)} L ${xOf(n - 1)} ${MT + PH} L ${xOf(0)} ${MT + PH} Z`;

  const totalLine = buildLine(trend.map((b) => b.total));
  const totalArea = buildArea(trend.map((b) => b.total));
  const phishLine = buildLine(trend.map((b) => b.phishing));
  const phishArea = buildArea(trend.map((b) => b.phishing));

  // Show labels for first, last, and a couple of middle points
  const labelIndices = new Set([0, Math.floor(n / 3), Math.floor((2 * n) / 3), n - 1]);
  const dayLabels = trend.map((b, i) => ({
    label: new Date(b.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    visible: labelIndices.has(i),
  }));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-base">trending_up</span>
          Detection Trends
          <span className="text-[10px] font-normal text-slate-500 normal-case tracking-normal">
            — last {n} days
          </span>
        </h3>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-2 h-2 rounded-full bg-primary inline-block" />
            All Scans
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
            Phishing
          </span>
        </div>
      </div>

      {/* Chart */}
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        style={{ height: 120 }}
        aria-label="Scan trend chart"
      >
        <defs>
          <linearGradient id="trend-total-grad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#135bec" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#135bec" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="trend-phish-grad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Subtle grid */}
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <line
            key={f}
            x1={ML} x2={W - MR}
            y1={MT + (1 - f) * PH}
            y2={MT + (1 - f) * PH}
            stroke="white" strokeWidth="1" opacity="0.04"
          />
        ))}

        <path d={totalArea} fill="url(#trend-total-grad)" />
        <path d={totalLine} fill="none" stroke="#135bec" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d={phishArea} fill="url(#trend-phish-grad)" />
        <path d={phishLine} fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="5 3" />

        {trend.map((b, i) => (
          <circle key={i} cx={xOf(i)} cy={yOf(b.total)} r="3" fill="#135bec" />
        ))}
      </svg>

      {/* X-axis labels */}
      <div className="flex justify-between mt-2">
        {dayLabels.map(({ label, visible }, i) => (
          <span key={i} className={`text-[10px] font-medium transition-opacity ${
            visible ? "text-slate-500 opacity-100" : "opacity-0"
          }`}>
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
