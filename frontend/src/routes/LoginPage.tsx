import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { z } from "zod";
import { useAuth } from "../hooks/useAuth";
import { apiClient, getApiError, getApiStatus } from "../lib/apiClient";

// ── Schema ──────────────────────────────────────────────────────────────────

const loginSchema = z.object({
  email: z.string().min(1, "Username or email is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

interface LoginResponse {
  token: string;
  user: { id: number; email: string };
}

// ── Component ────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const { login } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  const mutation = useMutation({
    mutationFn: (data: LoginFormValues) =>
      apiClient.post<LoginResponse>("/login", data).then((r) => r.data),
    onSuccess: (data) => {
      login(data.token);
    },
  });

  const onSubmit = (values: LoginFormValues) => mutation.mutate(values);

  const errorMsg = mutation.error
    ? getApiStatus(mutation.error) === 401
      ? "Invalid email or password."
      : getApiError(mutation.error)
    : null;

  return (
    <div className="bg-mesh min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-4xl text-primary">
              security
            </span>
            <span className="text-2xl font-bold text-white tracking-tight">
              Phishing<span className="text-primary">Shield</span>
            </span>
          </div>
        </div>

        {/* Card */}
        <div className="bg-surface border border-white/10 rounded-2xl p-8 shadow-xl">
          <h1 className="text-2xl font-semibold text-white mb-1">
            Welcome back
          </h1>
          <p className="text-sm text-gray-400 mb-6">
            Sign in to your account to continue
          </p>

          {errorMsg && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              <span className="material-symbols-outlined text-base">error</span>
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Username or Email
              </label>
              <input
                type="text"
                autoComplete="username"
                {...register("email")}
                className={`w-full rounded-lg border bg-white/5 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none transition
                  focus:ring-2 focus:ring-primary focus:border-transparent
                  ${errors.email ? "border-red-500" : "border-white/10"}`}
                placeholder="you@example.com or Admin"
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-400">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Password
              </label>
              <input
                type="password"
                autoComplete="current-password"
                {...register("password")}
                className={`w-full rounded-lg border bg-white/5 px-4 py-2.5 text-sm text-white placeholder-gray-500 outline-none transition
                  focus:ring-2 focus:ring-primary focus:border-transparent
                  ${errors.password ? "border-red-500" : "border-white/10"}`}
                placeholder="••••••••"
              />
              {errors.password && (
                <p className="mt-1 text-xs text-red-400">{errors.password.message}</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting || mutation.isPending}
              className="mt-2 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition
                hover:bg-primary/90 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-gray-400">
            Don't have an account?{" "}
            <Link to="/register" className="text-primary hover:underline font-medium">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
