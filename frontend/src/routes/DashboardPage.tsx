// src/routes/DashboardPage.tsx
import { useEffect, useMemo, useState } from "react";
import { useScanHistory } from "../hooks/useScanHistory";
import { useUserSummary } from "../hooks/useUserSummary";
import { useEmailAlerts } from "../hooks/useEmailAlerts";
import { decodeToken } from "../lib/auth";
import AuthHeader from "../components/AuthHeader";
import EmailAlertsToggle from "../components/EmailAlertsToggle";
import FirstLoginSetupModal from "../components/FirstLoginSetupModal";
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
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [dashboardNotice, setDashboardNotice] = useState<string | null>(null);
  const { data, isLoading, isError, error, refetch } =
    useScanHistory(50);
  const emailAlertsQuery = useEmailAlerts();
  const summaryQuery = useUserSummary();
  const latestScanId = useMemo(() => data?.[0]?.email_event_id ?? null, [data]);

  const firstSetupKey = useMemo(() => {
    const payload = decodeToken();
    if (!payload?.sub) {
      return null;
    }
    return `phishing_shield_setup_seen_${payload.sub}`;
  }, []);

  useEffect(() => {
    if (!firstSetupKey) {
      return;
    }
    const seen = localStorage.getItem(firstSetupKey) === "1";
    if (!seen) {
      setShowSetupModal(true);
    }
  }, [firstSetupKey]);

  useEffect(() => {
    if (!data || data.length === 0) {
      return;
    }

    // Keep browser notifications tied to the dashboard page lifecycle.
    const seenKey = "phishing_shield_seen_dashboard_scan_ids";
    const raw = sessionStorage.getItem(seenKey);

    if (!raw) {
      sessionStorage.setItem(
        seenKey,
        JSON.stringify(data.map((record) => record.email_event_id))
      );
      return;
    }

    const seen = new Set<number>((raw ? JSON.parse(raw) : []) as number[]);

    const unseenRecords = data.filter((record) => !seen.has(record.email_event_id));
    data.forEach((record) => seen.add(record.email_event_id));
    sessionStorage.setItem(seenKey, JSON.stringify(Array.from(seen)));

    if (unseenRecords.length === 0) {
      return;
    }

    const newPhishing = unseenRecords.filter(
      (record) => record.prediction?.predicted_label === "phishing"
    ).length;

    if (newPhishing > 0) {
      setDashboardNotice(
        `${unseenRecords.length} new scan${unseenRecords.length > 1 ? "s" : ""} received (${newPhishing} phishing)`
      );
    } else {
      setDashboardNotice(
        `${unseenRecords.length} new scan${unseenRecords.length > 1 ? "s" : ""} received`
      );
    }

    if (!emailAlertsQuery.data?.email_alerts_enabled) {
      return;
    }

    if (!("Notification" in window)) {
      return;
    }

    const showNotifications = () => {
      unseenRecords.slice(0, 3).forEach((record) => {
        const isPhishing = record.prediction?.predicted_label === "phishing";
        new Notification(isPhishing ? "Phishing Alert" : "New Email Scan", {
          body: isPhishing
            ? `Suspicious email from ${record.sender_domain}`
            : `Scanned email from ${record.sender_domain}`,
          tag: `scan-${record.email_event_id}`,
        });
      });
    };

    if (Notification.permission === "granted") {
      showNotifications();
      return;
    }

    if (Notification.permission === "default") {
      void Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          showNotifications();
        }
      });
    }
  }, [data, emailAlertsQuery.data?.email_alerts_enabled]);

  useEffect(() => {
    if (latestScanId == null) {
      return;
    }
    void summaryQuery.refetch();
  }, [latestScanId, summaryQuery]);

  function handleFinishSetup() {
    if (firstSetupKey) {
      localStorage.setItem(firstSetupKey, "1");
    }
    setShowSetupModal(false);
  }

  return (
    <div className="min-h-screen bg-mesh text-slate-100 font-display">
      <FirstLoginSetupModal open={showSetupModal} onFinish={handleFinishSetup} />

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

        {dashboardNotice && (
          <div className="flex items-center justify-between gap-3 rounded-xl border border-primary/30 bg-primary/10 px-4 py-3">
            <p className="text-sm font-medium text-slate-100 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-lg">notifications</span>
              {dashboardNotice}
            </p>
            <button
              onClick={() => setDashboardNotice(null)}
              className="text-xs font-semibold text-slate-300 hover:text-white"
            >
              Dismiss
            </button>
          </div>
        )}

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
