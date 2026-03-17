import { useState } from "react";
import { Link } from "react-router-dom";
import RegisterForm from "../components/RegisterForm";

export default function RegisterPage() {
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  if (registeredEmail) {
    return (
      <div className="relative flex min-h-screen w-full flex-col items-center justify-center bg-mesh px-6 py-12">
        <div className="w-full max-w-[480px] flex flex-col items-center text-center">
          {/* Success icon */}
          <div className="flex items-center justify-center size-20 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 mb-6 shadow-2xl shadow-emerald-500/10">
            <span className="material-symbols-outlined text-emerald-400 text-5xl">
              check_circle
            </span>
          </div>

          <h1 className="text-white text-3xl font-bold tracking-tight mb-3">
            Registration Successful
          </h1>

          <p className="text-slate-400 text-sm leading-relaxed mb-8 max-w-[340px]">
            Your account{" "}
            <span className="text-slate-200 font-semibold">
              {registeredEmail}
            </span>{" "}
            has been created. Please configure your email forwarding to start
            scanning for phishing threats.
          </p>

          {/* Next steps card */}
          <div className="w-full rounded-xl border border-slate-800 bg-slate-900/50 p-5 text-left space-y-3 backdrop-blur-sm">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-base">
                list_alt
              </span>
              Next Steps
            </p>
            <ol className="space-y-3">
              {[
                {
                  icon: "forward_to_inbox",
                  text: "Configure email forwarding in your mail client to route emails through Phishing Shield",
                },
                {
                  icon: "settings",
                  text: "Set your notification preferences and alert thresholds",
                },
                {
                  icon: "shield_lock",
                  text: "Start monitoring — your inbox will be protected within minutes",
                },
              ].map(({ icon, text }, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="flex-shrink-0 flex items-center justify-center size-7 rounded-lg bg-primary/10 border border-primary/20">
                    <span className="material-symbols-outlined text-primary text-sm">
                      {icon}
                    </span>
                  </span>
                  <span className="text-slate-300 text-sm leading-relaxed">
                    {text}
                  </span>
                </li>
              ))}
            </ol>
          </div>

          <Link
            to="/login"
            className="mt-6 w-full h-14 bg-primary hover:bg-primary/90 active:scale-[0.98] text-white font-bold rounded-xl transition-all shadow-lg shadow-primary/25 flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-xl">login</span>
            Go to Login
          </Link>

          <div className="mt-4 flex items-center gap-2 px-4 py-2 bg-slate-900/40 rounded-full border border-slate-800/50">
            <span className="material-symbols-outlined text-primary text-base">
              verified_user
            </span>
            <span className="text-slate-400 text-[10px] uppercase tracking-[0.15em] font-bold">
              End-to-End Encrypted Session
            </span>
          </div>
        </div>

        <BackgroundGlow />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center justify-center bg-mesh px-6 py-12">
      <div className="w-full max-w-[480px] flex flex-col">
        {/* Brand header */}
        <div className="flex flex-col items-center mb-10">
          <div className="relative flex items-center justify-center size-20 rounded-2xl bg-primary/10 border border-primary/20 mb-6 shadow-2xl shadow-primary/10">
            <span className="material-symbols-outlined text-primary text-5xl">
              shield_lock
            </span>
            <div className="absolute -top-1 -right-1 bg-primary rounded-full p-1 border-2 border-background-dark shadow-lg">
              <span className="material-symbols-outlined text-white text-[10px] font-bold">
                bolt
              </span>
            </div>
          </div>
          <h1 className="text-white text-3xl font-bold tracking-tight">
            Phishing Shield
          </h1>
          <p className="text-slate-400 text-sm mt-2 font-medium">
            Create your account to start protecting your inbox
          </p>
        </div>

        {/* Card */}
        <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-xl p-6 sm:p-8 shadow-2xl shadow-black/40">
          <div className="mb-6">
            <h2 className="text-white text-xl font-bold">Create Account</h2>
            <p className="text-slate-400 text-sm mt-1">
              Fill in your details below. Only email and password are required.
            </p>
          </div>

          <RegisterForm onSuccess={(email) => setRegisteredEmail(email)} />
        </div>

        {/* Footer note */}
        <div className="mt-8 w-full pt-6 border-t border-slate-800/60 flex flex-col items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-slate-900/40 rounded-full border border-slate-800/50">
            <span className="material-symbols-outlined text-primary text-base">
              verified_user
            </span>
            <span className="text-slate-400 text-[10px] uppercase tracking-[0.15em] font-bold">
              End-to-End Encrypted Session
            </span>
          </div>
        </div>
      </div>

      <BackgroundGlow />
    </div>
  );
}

function BackgroundGlow() {
  return (
    <div className="fixed bottom-0 left-0 w-full h-1/3 -z-10 opacity-20 pointer-events-none overflow-hidden">
      <div
        className="w-full h-full bg-primary blur-3xl opacity-30 scale-125"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(19,91,236,0.4) 0%, transparent 70%)",
        }}
      />
    </div>
  );
}
