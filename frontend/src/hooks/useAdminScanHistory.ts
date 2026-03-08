// src/hooks/useAdminScanHistory.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient, getApiError, getApiStatus } from "../lib/apiClient";
import type { AdminQueryError } from "./useAdminMetrics";

export interface AdminPrediction {
  prediction_id: number;
  model_version: string;
  phishing_probability: number;
  predicted_label: "phishing" | "legitimate";
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  created_at: string;
}

export interface AdminScanRecord {
  email_event_id: number;
  user_id: number;
  user_email: string;
  sender_domain: string;
  is_forwarded: boolean;
  received_at: string;
  message_id_hash: string | null;
  prediction: AdminPrediction | null;
}

async function fetchAdminScanHistory(limit: number): Promise<AdminScanRecord[]> {
  const response = await apiClient.get<AdminScanRecord[]>("/admin/predictions", {
    params: { limit },
  });
  return response.data;
}

export function useAdminScanHistory(limit = 100) {
  return useQuery<AdminScanRecord[], AdminQueryError>({
    queryKey: ["adminScanHistory", limit],
    queryFn: async () => {
      try {
        return await fetchAdminScanHistory(limit);
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
