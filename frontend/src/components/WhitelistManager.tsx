import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  useAddWhitelist,
  useRemoveWhitelist,
  useUserWhitelist,
} from "../hooks/useWhitelist";
import { getApiError } from "../lib/apiClient";

// ── Validation ────────────────────────────────────────────────────────────────

const addSchema = z.object({
  domain: z
    .string()
    .min(3, "Domain is required")
    .max(253)
    .regex(
      /^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$/,
      "Enter a valid domain (e.g. accounts.google.com)"
    ),
  reason: z.string().max(300).optional(),
});

type AddFormValues = z.infer<typeof addSchema>;

// ── Sub-components ────────────────────────────────────────────────────────────

function DomainRow({
  domain,
  reason,
  onRemove,
  removing,
}: {
  domain: string;
  reason: string;
  onRemove: () => void;
  removing: boolean;
}) {
  return (
    <li className="flex items-start justify-between gap-3 py-3 border-b border-white/5 last:border-0">
      <div className="min-w-0">
        <p className="text-sm font-medium text-white truncate">{domain}</p>
        {reason && (
          <p className="text-xs text-gray-400 mt-0.5 truncate">{reason}</p>
        )}
      </div>
      <button
        onClick={onRemove}
        disabled={removing}
        className="flex-shrink-0 flex items-center gap-1 rounded-lg border border-red-500/30 bg-red-500/10
          px-2.5 py-1 text-xs font-medium text-red-400 transition
          hover:bg-red-500/20 hover:border-red-400/50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="material-symbols-outlined text-sm">delete</span>
        Remove
      </button>
    </li>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function WhitelistManager() {
  const { data: domains, isLoading, isError } = useUserWhitelist();
  const addMutation = useAddWhitelist();
  const removeMutation = useRemoveWhitelist();
  const [removingDomain, setRemovingDomain] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AddFormValues>({ resolver: zodResolver(addSchema) });

  const onAdd = (values: AddFormValues) => {
    addMutation.mutate(
      { domain: values.domain.toLowerCase().trim(), reason: values.reason ?? "" },
      { onSuccess: () => reset() }
    );
  };

  const onRemove = (domain: string) => {
    setRemovingDomain(domain);
    removeMutation.mutate(domain, {
      onSettled: () => setRemovingDomain(null),
    });
  };

  return (
    <section className="space-y-3">
      {/* Section header */}
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-base">
            verified_user
          </span>
          Trusted Domains
        </h2>
        {domains.length > 0 && (
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[11px] font-bold">
            {domains.length}
          </span>
        )}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        {/* Add form */}
        <div className="p-5 border-b border-slate-800">
          <p className="text-xs text-slate-400 mb-3">
            Emails from trusted domains are always marked as{" "}
            <span className="text-green-400 font-medium">legitimate</span> and
            bypass the ML model.
          </p>

          {addMutation.error && (
            <div className="mb-3 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
              <span className="material-symbols-outlined text-sm">error</span>
              {getApiError(addMutation.error)}
            </div>
          )}

          <form onSubmit={handleSubmit(onAdd)} noValidate>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1 min-w-0">
                <input
                  type="text"
                  placeholder="accounts.google.com"
                  {...register("domain")}
                  className={`w-full rounded-lg border bg-white/5 px-3 py-2 text-sm text-white placeholder-gray-500
                    outline-none transition focus:ring-2 focus:ring-primary focus:border-transparent
                    ${errors.domain ? "border-red-500" : "border-white/10"}`}
                />
                {errors.domain && (
                  <p className="mt-1 text-xs text-red-400">{errors.domain.message}</p>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <input
                  type="text"
                  placeholder="Reason (optional)"
                  {...register("reason")}
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white
                    placeholder-gray-500 outline-none transition focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                disabled={addMutation.isPending}
                className="flex-shrink-0 flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm
                  font-semibold text-white transition hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-base">
                  {addMutation.isPending ? "hourglass_empty" : "add"}
                </span>
                {addMutation.isPending ? "Adding…" : "Add"}
              </button>
            </div>
          </form>
        </div>

        {/* Domain list */}
        <div className="px-5">
          {isLoading && (
            <div className="flex items-center gap-2 py-6 text-slate-400 text-sm">
              <span className="material-symbols-outlined text-xl animate-spin">progress_activity</span>
              Loading trusted domains…
            </div>
          )}

          {isError && (
            <p className="py-5 text-sm text-red-400 text-center">
              Failed to load trusted domains.
            </p>
          )}

          {!isLoading && !isError && domains.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-8 text-center text-slate-500">
              <span className="material-symbols-outlined text-3xl">shield_question</span>
              <p className="text-sm">Add your first trusted domain</p>
            </div>
          )}

          {!isLoading && !isError && domains.length > 0 && (
            <ul>
              {domains.map((item) => (
                <DomainRow
                  key={item.id}
                  domain={item.domain}
                  reason={item.reason}
                  onRemove={() => onRemove(item.domain)}
                  removing={removingDomain === item.domain && removeMutation.isPending}
                />
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
