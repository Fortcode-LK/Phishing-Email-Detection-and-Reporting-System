import { useEmailAlerts, useSetEmailAlerts } from "../hooks/useEmailAlerts";

type FirstLoginSetupModalProps = {
  open: boolean;
  onFinish: () => void;
};

export default function FirstLoginSetupModal({
  open,
  onFinish,
}: FirstLoginSetupModalProps) {
  const { data, isLoading } = useEmailAlerts();
  const mutation = useSetEmailAlerts();

  if (!open) {
    return null;
  }

  const enabled = data?.email_alerts_enabled ?? false;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onFinish}
      />

      <div className="relative w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="border-b border-slate-800 px-6 py-5">
          <h2 className="text-xl font-bold text-white">Welcome to Phishing Shield</h2>
          <p className="mt-1 text-sm text-slate-400">
            Complete this quick setup to start scanning forwarded emails.
          </p>
        </div>

        <div className="space-y-6 px-6 py-5">
          <section>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-300">
              Email Auto-Forwarding Setup
            </h3>
            <ol className="space-y-3 text-sm text-slate-300">
              <li className="flex gap-3">
                <span className="mt-0.5 inline-flex size-5 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                  1
                </span>
                Open your email provider settings and go to Forwarding.
              </li>
              <li className="flex gap-3">
                <span className="mt-0.5 inline-flex size-5 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                  2
                </span>
                Add your local scanner address as the forwarding target.
              </li>
              <li className="flex gap-3">
                <span className="mt-0.5 inline-flex size-5 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                  3
                </span>
                Save the rule and send a test email to verify scans appear in this dashboard.
              </li>
            </ol>
            <p className="mt-3 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-xs text-slate-400">
              Local scanner address: localhost:1025
            </p>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-800/40 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-white">Email Scan Notifications</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-400">
                  Enable this to receive a reply email containing the scan result after each analysed message.
                </p>
              </div>

              <button
                onClick={() => mutation.mutate(!enabled)}
                disabled={isLoading || mutation.isPending}
                aria-label={enabled ? "Disable email notifications" : "Enable email notifications"}
                className={[
                  "relative h-6 w-12 flex-shrink-0 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary/50",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  enabled ? "bg-primary" : "bg-slate-700",
                ].join(" ")}
              >
                <span
                  className={[
                    "absolute left-0.5 top-0.5 size-5 rounded-full bg-white shadow transition-transform duration-200",
                    enabled ? "translate-x-6" : "translate-x-0",
                  ].join(" ")}
                />
              </button>
            </div>

            {mutation.isError && (
              <p className="mt-3 text-xs text-red-400">Failed to update notification setting. Try again.</p>
            )}

            <p className={[
              "mt-3 text-xs font-medium",
              enabled ? "text-emerald-400" : "text-slate-500",
            ].join(" ")}>
              {enabled ? "Notifications enabled" : "Notifications disabled"}
            </p>
          </section>
        </div>

        <div className="flex items-center justify-end border-t border-slate-800 px-6 py-4">
          <button
            onClick={onFinish}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}