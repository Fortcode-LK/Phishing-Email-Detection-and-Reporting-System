// src/components/admin/TopSenderDomains.tsx
import type { TopSenderDomain } from "../../hooks/useAdminMetrics";

interface TopSenderDomainsProps {
  domains: TopSenderDomain[];
}

function PhishingRateBadge({ rate }: { rate: number }) {
  const pct = (rate * 100).toFixed(1);
  if (rate >= 0.6) {
    return (
      <span className="inline-flex px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 text-[11px] font-bold">
        {pct}%
      </span>
    );
  }
  if (rate >= 0.25) {
    return (
      <span className="inline-flex px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 text-[11px] font-bold">
        {pct}%
      </span>
    );
  }
  return (
    <span className="inline-flex px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-bold">
      {pct}%
    </span>
  );
}

export default function TopSenderDomains({ domains }: TopSenderDomainsProps) {
  if (domains.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-sm">
        No sender domain data available.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-800 flex items-center gap-2">
        <span className="material-symbols-outlined text-primary text-base">
          domain
        </span>
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
          Top Sender Domains
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left min-w-[480px]">
          <thead className="bg-slate-800/60 border-b border-slate-800">
            <tr>
              {["Domain", "Total", "Phishing", "Phishing Rate"].map((col) => (
                <th
                  key={col}
                  className="px-5 py-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {domains.map((d, i) => {
              const rate = d.count > 0 ? d.phishing_count / d.count : 0;
              return (
                <tr
                  key={d.domain}
                  className={
                    i % 2 === 0
                      ? "bg-transparent hover:bg-slate-800/30 transition-colors"
                      : "bg-slate-800/20 hover:bg-slate-800/40 transition-colors"
                  }
                >
                  <td className="px-5 py-3.5 text-sm font-mono text-slate-200 whitespace-nowrap">
                    {d.domain}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-slate-300 whitespace-nowrap">
                    {d.count.toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5 text-sm text-slate-300 whitespace-nowrap">
                    {d.phishing_count.toLocaleString()}
                  </td>
                  <td className="px-5 py-3.5 whitespace-nowrap">
                    <PhishingRateBadge rate={rate} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
