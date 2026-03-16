import { useEmailAlerts, useSetEmailAlerts } from "../hooks/useEmailAlerts";

export default function EmailAlertsToggle() {
  const { data, isLoading } = useEmailAlerts();
  const mutation = useSetEmailAlerts();

  const enabled = data?.email_alerts_enabled ?? false;

  async function handleToggle() {
    const nextEnabled = !enabled;

    // Ask notification permission from a click handler so browsers allow the prompt.
    if (
      nextEnabled &&
      "Notification" in window &&
      Notification.permission === "default"
    ) {
      try {
        await Notification.requestPermission();
      } catch {
        // Ignore prompt failures and still save the alert preference.
      }
    }

    mutation.mutate(nextEnabled);
  }

  return (
    <div className="w-full rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          <div className="flex-shrink-0 flex items-center justify-center size-9 rounded-lg bg-primary/10 border border-primary/20 mt-0.5">
            <span className="material-symbols-outlined text-primary text-lg">
              notifications
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white">Email Scan Alerts</p>
            <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
              Receive an email reply with scan results whenever a forwarded email is analysed.
            </p>
          </div>
        </div>

        <button
          onClick={handleToggle}
          disabled={isLoading || mutation.isPending}
          aria-label={enabled ? "Disable email alerts" : "Enable email alerts"}
          className={[
            "relative flex-shrink-0 w-12 h-6 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary/50",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            enabled ? "bg-primary" : "bg-slate-700",
          ].join(" ")}
        >
          <span
            className={[
              "absolute top-0.5 left-0.5 size-5 rounded-full bg-white shadow transition-transform duration-200",
              enabled ? "translate-x-6" : "translate-x-0",
            ].join(" ")}
          />
        </button>
      </div>

      {mutation.isError && (
        <p className="mt-3 text-xs text-red-400 flex items-center gap-1">
          <span className="material-symbols-outlined text-sm">error</span>
          Failed to update — please try again.
        </p>
      )}

      <p className={[
        "mt-3 text-xs font-medium flex items-center gap-1.5 transition-colors",
        enabled ? "text-emerald-400" : "text-slate-500",
      ].join(" ")}>
        <span className="material-symbols-outlined text-sm">
          {enabled ? "check_circle" : "notifications_off"}
        </span>
        {enabled ? "Alerts are enabled" : "Alerts are disabled"}
      </p>
    </div>
  );
}
