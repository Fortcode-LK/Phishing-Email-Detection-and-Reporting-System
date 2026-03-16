// src/hooks/useScanHistory.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient, getApiError, getApiStatus } from "../lib/apiClient";

export interface Prediction {
  prediction_id: number;
  model_version: string;
  phishing_probability: number;
  predicted_label: "phishing" | "legitimate";
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  created_at: string;
}

export interface ScanRecord {
  email_event_id: number;
  user_id: number;
  sender_domain: string;
  is_forwarded: boolean;
  received_at: string;
  message_id_hash: string;
  prediction: Prediction | null;
}

export interface ScanHistoryError {
  status: number | undefined;
  message: string;
}

async function fetchScanHistory(limit: number): Promise<ScanRecord[]> {
  const response = await apiClient.get<ScanRecord[]>("/predictions", {
    params: { limit },
  });
  return response.data;
}

export function useScanHistory(limit = 50) {
  return useQuery<ScanRecord[], ScanHistoryError>({
    queryKey: ["scanHistory", limit],
    queryFn: async () => {
      try {
        return await fetchScanHistory(limit);
      } catch (err: unknown) {
        const status = getApiStatus(err);
        const message = getApiError(err);
        throw { status, message } satisfies ScanHistoryError;
      }
    },
    staleTime: 1000 * 5, // Keep data fresh for near-real-time dashboard updates
    refetchInterval: 1000 * 5, // Poll while dashboard is open
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 1,
  });
}
