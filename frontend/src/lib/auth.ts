/**
 * Thin helpers for managing the JWT stored in localStorage.
 * The payload shape is { sub: string, email: string, exp: number, iat: number }.
 */

const TOKEN_KEY = "phishing_shield_token";

export interface TokenPayload {
  sub: string;   // user_id as string
  email: string;
  role: string;  // "admin" | "normal"
  exp: number;
  iat: number;
}

/** Persist a JWT in localStorage. */
export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/** Retrieve the stored JWT (or null if not present). */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/** Remove the JWT from localStorage. */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Decode the JWT payload without verifying the signature.
 * Returns null if the token is missing or malformed.
 */
export function decodeToken(): TokenPayload | null {
  const token = getToken();
  if (!token) return null;
  try {
    const base64Payload = token.split(".")[1];
    const json = atob(base64Payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json) as TokenPayload;
  } catch {
    return null;
  }
}

/**
 * Returns true when a non-expired JWT is present.
 * Expiry is checked client-side (in seconds since epoch).
 */
export function isAuthenticated(): boolean {
  const payload = decodeToken();
  if (!payload) return false;
  return payload.exp * 1000 > Date.now();
}
