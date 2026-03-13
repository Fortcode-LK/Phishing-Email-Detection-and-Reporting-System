// src/hooks/useAdminMetrics.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient, getApiError, getApiStatus } from "../lib/apiClient";

export interface TopSenderDomain {
  domain: string;
  count: number;
  phishing_count: number;
}

export interface AdminMetrics {
  total_scanned: number;
  total_phishing: number;
  total_legitimate: number;
  phishing_ratio: number;
  top_sender_domains: TopSenderDomain[];
}

export interface AdminQueryError {
  status: number | undefined;
  message: string;
}

async function fetchAdminMetrics(): Promise<AdminMetrics> {
  const response = await apiClient.get<AdminMetrics>("/admin/metrics");
  return response.data;
}

export function useAdminMetrics() {
  return useQuery<AdminMetrics, AdminQueryError>({
    queryKey: ["adminMetrics"],
    queryFn: async () => {
      try {
        return await fetchAdminMetrics();
      } catch (err: unknown) {
        const status = getApiStatus(err);
        const message = getApiError(err);
        throw { status, message } satisfies AdminQueryError;
      }
    },
    staleTime: 1000 * 45,
    retry: 1,
  });
}
