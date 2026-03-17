import { useAuth } from "../hooks/useAuth";

interface AuthHeaderProps {
  /** Optional label shown in the breadcrumb area after the logo. */
  title?: string;
}

/**
 * Sticky top navigation bar that shows the Phishing Shield logo on the left
 * and user info + a logout button on the right.  Used by every protected page.
 */
export default function AuthHeader({ title }: AuthHeaderProps) {
  const { userEmail, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-white/10 bg-surface/80 px-6 py-3 backdrop-blur-sm">
      {/* Left — logo + optional page title */}
      <div className="flex items-center gap-3">
        <span className="material-symbols-outlined text-2xl text-primary">
          security
        </span>
        <span className="text-base font-bold text-white tracking-tight">
          Phishing<span className="text-primary">Shield</span>
        </span>
        {title && (
          <>
            <span className="text-white/20">/</span>
            <span className="text-sm text-gray-400">{title}</span>
          </>
        )}
      </div>

      {/* Right — user info + logout */}
      <div className="flex items-center gap-3">
        {userEmail && (
          <span className="hidden sm:block text-xs text-gray-400 max-w-[180px] truncate">
            {userEmail}
          </span>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5
            text-xs font-medium text-gray-300 transition hover:bg-white/10 hover:text-white active:scale-95"
        >
          <span className="material-symbols-outlined text-base">logout</span>
          Sign out
        </button>
      </div>
    </header>
  );
}
