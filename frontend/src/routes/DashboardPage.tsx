// src/routes/DashboardPage.tsx
import { useScanHistory } from "../hooks/useScanHistory";
import { useUserSummary } from "../hooks/useUserSummary";
import AuthHeader from "../components/AuthHeader";
import EmailAlertsToggle from "../components/EmailAlertsToggle";
import WhitelistManager from "../components/WhitelistManager";
import ScanTrendChart from "../components/charts/ScanTrendChart";
import RiskDonutChart from "../components/charts/RiskDonutChart";
import SummaryCards from "../components/dashboard/SummaryCards";
import ScanTable from "../components/dashboard/ScanTable";

function Spinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-slate-400">
      <span className="material-symbols-outlined text-5xl text-primary animate-spin">
        progress_activity
      </span>
      <p className="text-sm font-medium">Loading scan history…</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <div className="flex items-center justify-center size-16 rounded-2xl bg-slate-800 border border-slate-700 mb-2">
        <span className="material-symbols-outlined text-slate-500 text-4xl">
          inbox
        </span>
      </div>
      <h3 className="text-white font-semibold text-lg">No scans yet</h3>
      <p className="text-slate-400 text-sm max-w-xs leading-relaxed">
        You haven't scanned any emails yet. Configure email forwarding to start
        detecting phishing threats.
      </p>
    </div>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col sm:flex-row items-start sm:items-center gap-4 rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4"
    >
      <span className="material-symbols-outlined text-red-400 text-2xl flex-shrink-0">
        warning
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-red-300 text-sm font-semibold">
          Failed to load scan history
        </p>
        <p className="text-red-400/70 text-xs mt-0.5">{message}</p>
      </div>
      <button
        onClick={onRetry}
        className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-300 text-sm font-semibold transition-colors"
      >
        <span className="material-symbols-outlined text-base">refresh</span>
        Retry
      </button>
    </div>
  );
}

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } =
    useScanHistory(50);
  const summaryQuery = useUserSummary();

  return (
    <div className="min-h-screen bg-mesh text-slate-100 font-display">
      {/* Top bar */}
      <AuthHeader title="Dashboard" />

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Heading */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            My Scan History
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Overview of all emails analysed by Phishing Shield.
          </p>
        </div>

        {/* Summary cards — driven by full DB aggregates */}
        {summaryQuery.data && <SummaryCards summary={summaryQuery.data} />}

        {/* Charts row — trend + risk breakdown */}
        {summaryQuery.data && summaryQuery.data.total_scanned > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ScanTrendChart trend={summaryQuery.data.daily_trend} />
            <RiskDonutChart summary={summaryQuery.data} />
          </div>
        )}

        {/* Trusted domains whitelist */}
        <WhitelistManager />

        {/* Email scan alerts toggle */}
        <EmailAlertsToggle />

        {/* States */}
        {isLoading && <Spinner />}

        {isError && (
          <ErrorState
            message={
              error?.message ??
              "Unexpected error, please try again later."
            }
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !isError && data && data.length === 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl">
            <EmptyState />
          </div>
        )}

        {/* Table */}
        {!isLoading && !isError && data && data.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-base">
                  list_alt
                </span>
                Email Records
                <span className="ml-1 px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[11px] font-bold">
                  {data.length}
                </span>
              </h2>
            </div>
            <ScanTable data={data} />
          </div>
        )}
      </main>

      {/* Background glow */}
      <div className="fixed bottom-0 left-0 w-full h-1/3 -z-10 opacity-20 pointer-events-none overflow-hidden">
        <div
          className="w-full h-full blur-3xl opacity-30 scale-125"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(19,91,236,0.4) 0%, transparent 70%)",
          }}
        />
      </div>
    </div>
  );
}
