import { useCallback, useState } from "react";
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
  // Initialise from whatever is already in localStorage
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
    setState({ isLoggedIn: false, userId: null, userEmail: null });
    navigate("/login");
  }, [navigate]);

  return { ...state, login, logout };
}
