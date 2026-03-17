import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  decodeToken,
  isAuthenticated,
  removeToken,
  saveToken,
} from "../lib/auth";

export interface AuthState {
  isLoggedIn: boolean;
  userId: number | null;
  userEmail: string | null;
  login: (token: string) => void;
  logout: () => void;
}

export function useAuth(): AuthState {
  const [state, setState] = useState<{
    isLoggedIn: boolean;
    userId: number | null;
    userEmail: string | null;
  }>(() => {
    if (!isAuthenticated()) {
      return { isLoggedIn: false, userId: null, userEmail: null };
    }
    const payload = decodeToken();
    return {
      isLoggedIn: true,
      userId: payload ? parseInt(payload.sub, 10) : null,
      userEmail: payload?.email ?? null,
    };
  });

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const login = useCallback(
    (token: string) => {
      saveToken(token);
      const payload = decodeToken();
      setState({
        isLoggedIn: true,
        userId: payload ? parseInt(payload.sub, 10) : null,
        userEmail: payload?.email ?? null,
      });
      navigate(payload?.role === "admin" ? "/admin" : "/dashboard");
    },
    [navigate]
  );

  const logout = useCallback(() => {
    removeToken();
    queryClient.clear();
    setState({ isLoggedIn: false, userId: null, userEmail: null });
    navigate("/login");
  }, [navigate, queryClient]);

  return { ...state, login, logout };
}
