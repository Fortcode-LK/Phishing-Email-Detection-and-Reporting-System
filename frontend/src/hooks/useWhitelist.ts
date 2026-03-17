import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, getApiError } from "../lib/apiClient";

export interface WhitelistItem {
  id: number;
  domain: string;
  reason: string;
  created_at: string;
}

export interface AddWhitelistPayload {
  domain: string;
  reason?: string;
}

const QUERY_KEY = ["whitelist"] as const;

// ── Queries ──────────────────────────────────────────────────────────────────

export function useUserWhitelist() {
  const { data, isLoading, isError, error, refetch } = useQuery<WhitelistItem[]>({
    queryKey: QUERY_KEY,
    queryFn: () =>
      apiClient.get<WhitelistItem[]>("/whitelist").then((r) => r.data),
  });
  return { data: data ?? [], isLoading, isError, error, refetch };
}

// ── Mutations ─────────────────────────────────────────────────────────────────

export function useAddWhitelist() {
  const qc = useQueryClient();
  return useMutation<WhitelistItem, Error, AddWhitelistPayload>({
    mutationFn: (payload) =>
      apiClient.post<WhitelistItem>("/whitelist", payload).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
    onError: (err) => {
      throw new Error(getApiError(err));
    },
  });
}

export function useRemoveWhitelist() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (domain) =>
      apiClient.delete(`/whitelist/${encodeURIComponent(domain)}`).then(() => undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}
