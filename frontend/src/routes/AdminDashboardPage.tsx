// src/routes/AdminDashboardPage.tsx
import { useAdminMetrics } from "../hooks/useAdminMetrics";
import { useAdminScanHistory } from "../hooks/useAdminScanHistory";
import AuthHeader from "../components/AuthHeader";
import DomainBarChart from "../components/charts/DomainBarChart";
import AdminSummaryCards from "../components/admin/AdminSummaryCards";
import TopSenderDomains from "../components/admin/TopSenderDomains";
import AdminScanTable from "../components/admin/AdminScanTable";

function Spinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-slate-400">
      <span className="material-symbols-outlined text-5xl text-primary animate-spin">
        progress_activity
      </span>
      <p className="text-sm font-medium">Loading admin data…</p>
    </div>
  );
}

function UnauthorizedState() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <div className="flex items-center justify-center size-16 rounded-2xl bg-slate-800 border border-slate-700 mb-2">
        <span className="material-symbols-outlined text-amber-400 text-4xl">
          lock
        </span>
      </div>
      <h3 className="text-white font-semibold text-lg">Access Denied</h3>
      <p className="text-slate-400 text-sm max-w-xs leading-relaxed">
        You do not have access to this page.
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
          Failed to load admin data
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

function EmptyState() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl">
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <div className="flex items-center justify-center size-16 rounded-2xl bg-slate-800 border border-slate-700 mb-2">
          <span className="material-symbols-outlined text-slate-500 text-4xl">
            inbox
          </span>
        </div>
        <h3 className="text-white font-semibold text-lg">
          No emails scanned yet
        </h3>
        <p className="text-slate-400 text-sm max-w-xs leading-relaxed">
          No emails have been processed by the system yet.
        </p>
      </div>
    </div>
  );
}

export default function AdminDashboardPage() {
  const metricsQuery = useAdminMetrics();
  const historyQuery = useAdminScanHistory(100);

  const isLoading = metricsQuery.isLoading || historyQuery.isLoading;

  const metricsUnauthorized =
    metricsQuery.error?.status === 401 ||
    metricsQuery.error?.status === 403;
  const historyUnauthorized =
    historyQuery.error?.status === 401 ||
    historyQuery.error?.status === 403;
  const isUnauthorized = metricsUnauthorized || historyUnauthorized;

  const isError =
    !isUnauthorized &&
    (metricsQuery.isError || historyQuery.isError);

  const errorMessage =
    metricsQuery.error?.message ??
    historyQuery.error?.message ??
    "Unexpected error, please try again later.";

  function handleRetry() {
    if (metricsQuery.isError) metricsQuery.refetch();
    if (historyQuery.isError) historyQuery.refetch();
  }

  return (
    <div className="min-h-screen bg-mesh text-slate-100 font-display">
      {/* Top bar */}
      <AuthHeader title="Admin" />

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Heading */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Admin Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            System-wide phishing detection overview.
          </p>
        </div>

        {/* States */}
        {isLoading && <Spinner />}

        {!isLoading && isUnauthorized && <UnauthorizedState />}

        {!isLoading && isError && (
          <ErrorState message={errorMessage} onRetry={handleRetry} />
        )}

        {/* Content — only rendered when both queries succeeded */}
        {!isLoading && !isUnauthorized && !isError && metricsQuery.data && (
          <>
            {/* Summary cards */}
            <AdminSummaryCards metrics={metricsQuery.data} />

            {/* Domain volume bar chart */}
            {metricsQuery.data.top_sender_domains.length > 0 && (
              <DomainBarChart domains={metricsQuery.data.top_sender_domains} />
            )}

            {/* Top sender domains table */}
            <TopSenderDomains
              domains={metricsQuery.data.top_sender_domains}
            />

            {/* Scan history table */}
            {historyQuery.data && historyQuery.data.length === 0 ? (
              <EmptyState />
            ) : historyQuery.data && historyQuery.data.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary text-base">
                      list_alt
                    </span>
                    All Email Records
                    <span className="ml-1 px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[11px] font-bold">
                      {historyQuery.data.length}
                    </span>
                  </h2>
                </div>
                <AdminScanTable data={historyQuery.data} />
              </div>
            ) : null}
          </>
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
