// src/hooks/useUserSummary.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient, getApiError, getApiStatus } from "../lib/apiClient";

export interface DailyTrendPoint {
  date: string;    // YYYY-MM-DD
  total: number;
  phishing: number;
}

export interface UserSummary {
  total_scanned: number;
  total_phishing: number;
  total_legitimate: number;
  phishing_ratio: number;
  risk_high: number;
  risk_medium: number;
  risk_low: number;
  risk_unscanned: number;
  daily_trend: DailyTrendPoint[];
}

export interface UserSummaryError {
  status: number | undefined;
  message: string;
}

export function useUserSummary(trendDays = 14) {
  return useQuery<UserSummary, UserSummaryError>({
    queryKey: ["userSummary", trendDays],
    queryFn: async () => {
      try {
        const res = await apiClient.get<UserSummary>("/user/summary", {
          params: { trend_days: trendDays },
        });
        return res.data;
      } catch (err: unknown) {
        const status = getApiStatus(err);
        const message = getApiError(err);
        throw { status, message } satisfies UserSummaryError;
      }
    },
    staleTime: 1000 * 45,
    retry: 1,
  });
}
