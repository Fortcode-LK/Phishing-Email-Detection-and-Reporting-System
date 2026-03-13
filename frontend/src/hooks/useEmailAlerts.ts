import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";

interface EmailAlertsResponse {
  email_alerts_enabled: boolean;
}

const QUERY_KEY = ["emailAlerts"] as const;

export function useEmailAlerts() {
  return useQuery<EmailAlertsResponse>({
    queryKey: QUERY_KEY,
    queryFn: () =>
      apiClient.get<EmailAlertsResponse>("/user/alerts").then((r) => r.data),
  });
}

export function useSetEmailAlerts() {
  const qc = useQueryClient();
  return useMutation<EmailAlertsResponse, Error, boolean>({
    mutationFn: (enabled) =>
      apiClient
        .put<EmailAlertsResponse>("/user/alerts", { email_alerts_enabled: enabled })
        .then((r) => r.data),
    onSuccess: (data) => {
      qc.setQueryData(QUERY_KEY, data);
    },
  });
}
