// src/components/admin/AdminSummaryCards.tsx
import type { AdminMetrics } from "../../hooks/useAdminMetrics";

interface AdminSummaryCardsProps {
  metrics: AdminMetrics;
}

export default function AdminSummaryCards({ metrics }: AdminSummaryCardsProps) {
  const cards = [
    {
      label: "Total Scanned",
      value: metrics.total_scanned.toLocaleString(),
      icon: "mail",
      iconColor: "text-slate-400",
      iconBg: "bg-slate-800",
      borderAccent: "border-l-slate-500",
    },
    {
      label: "Phishing Detected",
      value: metrics.total_phishing.toLocaleString(),
      icon: "dangerous",
      iconColor: "text-red-400",
      iconBg: "bg-red-500/10",
      borderAccent: "border-l-red-500",
    },
    {
      label: "Legitimate",
      value: metrics.total_legitimate.toLocaleString(),
      icon: "check_circle",
      iconColor: "text-emerald-400",
      iconBg: "bg-emerald-500/10",
      borderAccent: "border-l-emerald-500",
    },
    {
      label: "Phishing Ratio",
      value: `${(metrics.phishing_ratio * 100).toFixed(1)}%`,
      icon: "percent",
      iconColor: "text-amber-400",
      iconBg: "bg-amber-500/10",
      borderAccent: "border-l-amber-500",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ label, value, icon, iconColor, iconBg, borderAccent }) => (
        <div
          key={label}
          className={`bg-slate-900 border border-slate-800 border-l-4 ${borderAccent} rounded-xl p-5 shadow-sm`}
        >
          <div className="flex items-center justify-between mb-3">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              {label}
            </p>
            <span
              className={`flex items-center justify-center size-8 rounded-lg ${iconBg}`}
            >
              <span
                className={`material-symbols-outlined text-lg ${iconColor}`}
              >
                {icon}
              </span>
            </span>
          </div>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
      ))}
    </div>
  );
}
