// src/components/dashboard/ScanTable.tsx
import type { ScanRecord } from "../../hooks/useScanHistory";

interface ScanTableProps {
  data: ScanRecord[];
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function VerdictBadge({
  label,
}: {
  label: "phishing" | "legitimate" | null;
}) {
  if (label === "phishing") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 text-[11px] font-bold uppercase tracking-wide">
        <span className="material-symbols-outlined text-sm">dangerous</span>
        Phishing
      </span>
    );
  }
  if (label === "legitimate") {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-bold uppercase tracking-wide">
        <span className="material-symbols-outlined text-sm">check_circle</span>
        Legitimate
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-700/60 text-slate-400 text-[11px] font-bold uppercase tracking-wide">
      <span className="material-symbols-outlined text-sm">help</span>
      Not Classified
    </span>
  );
}

function RiskBadge({ level }: { level: string | null }) {
  if (level === "HIGH") {
    return (
      <span className="inline-flex px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 text-[11px] font-bold">
        HIGH
      </span>
    );
  }
  if (level === "MEDIUM") {
    return (
      <span className="inline-flex px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 text-[11px] font-bold">
        MEDIUM
      </span>
    );
  }
  if (level === "LOW") {
    return (
      <span className="inline-flex px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-bold">
        LOW
      </span>
    );
  }
  return (
    <span className="text-slate-500 text-[11px] font-bold">N/A</span>
  );
}

export default function ScanTable({ data }: ScanTableProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left min-w-[640px]">
          <thead className="bg-slate-800/60 border-b border-slate-800">
            <tr>
              {[
                "Sender Domain",
                "Received At",
                "Verdict",
                "Risk Level",
                "Phishing Probability",
              ].map((col) => (
                <th
                  key={col}
                  className="px-5 py-3.5 text-[10px] font-bold text-slate-400 uppercase tracking-widest whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {data.map((record, i) => (
              <tr
                key={record.email_event_id}
                className={
                  i % 2 === 0
                    ? "bg-transparent hover:bg-slate-800/30 transition-colors"
                    : "bg-slate-800/20 hover:bg-slate-800/40 transition-colors"
                }
              >
                <td className="px-5 py-4 text-sm font-mono text-slate-200 whitespace-nowrap">
                  {record.sender_domain}
                </td>
                <td className="px-5 py-4 text-sm text-slate-400 whitespace-nowrap">
                  {formatDate(record.received_at)}
                </td>
                <td className="px-5 py-4 whitespace-nowrap">
                  <VerdictBadge
                    label={record.prediction?.predicted_label ?? null}
                  />
                </td>
                <td className="px-5 py-4 whitespace-nowrap">
                  <RiskBadge level={record.prediction?.risk_level ?? null} />
                </td>
                <td className="px-5 py-4 whitespace-nowrap" style={{ minWidth: 140 }}>
                  {record.prediction != null ? (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[11px] font-bold ${
                            record.prediction.phishing_probability >= 0.7
                              ? "text-red-400"
                              : record.prediction.phishing_probability >= 0.4
                              ? "text-amber-400"
                              : "text-emerald-400"
                          }`}
                        >
                          {(record.prediction.phishing_probability * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            record.prediction.phishing_probability >= 0.7
                              ? "bg-red-500"
                              : record.prediction.phishing_probability >= 0.4
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                          }`}
                          style={{
                            width: `${(record.prediction.phishing_probability * 100).toFixed(1)}%`,
                          }}
                        />
                      </div>
                    </div>
                  ) : (
                    <span className="text-slate-600">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
