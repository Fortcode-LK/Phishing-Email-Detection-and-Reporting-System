import { useMutation } from "@tanstack/react-query";
import { apiClient, getApiError, getApiStatus } from "../lib/apiClient";
import type { RegisterFormValues } from "../lib/validation";

export interface RegisterSuccessResponse {
  id: number;
  email: string;
}

export interface RegisterError {
  status: number | undefined;
  message: string;
}

async function registerUser(
  data: RegisterFormValues
): Promise<RegisterSuccessResponse> {
  const payload = {
    email: data.email,
    password: data.password,
    firstName: data.firstName || undefined,
    lastName: data.lastName || undefined,
    mobileNumber: data.mobileNumber || undefined,
    address: data.address || undefined,
  };

  const response = await apiClient.post<RegisterSuccessResponse>(
    "/register",
    payload
  );
  return response.data;
}

export function useRegister() {
  return useMutation<RegisterSuccessResponse, RegisterError, RegisterFormValues>(
    {
      mutationFn: async (data: RegisterFormValues) => {
        try {
          return await registerUser(data);
        } catch (err: unknown) {
          const status = getApiStatus(err);
          const message = getApiError(err);
          throw { status, message } satisfies RegisterError;
        }
      },
    }
  );
}
