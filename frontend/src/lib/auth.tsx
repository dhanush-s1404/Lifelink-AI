"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { apiFetch, apiPost, tokenManager } from "@/lib/api";

export type User = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at?: string;
};

type AuthResult = {
  user: User;
  tokens: { access_token: string; refresh_token: string; token_type: string; expires_in: number };
};

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const me = await apiFetch<User>("/users/me");
      setUser(me);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (tokenManager.getAccess() || tokenManager.getRefresh()) {
        await refreshUser();
      }
      if (!cancelled) setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string, rememberMe = false) => {
    const result = await apiPost<AuthResult>("/auth/login", { email, password, remember_me: rememberMe });
    tokenManager.setTokens(result.tokens.access_token, result.tokens.refresh_token);
    setUser(result.user);
  }, []);

  const register = useCallback(async (email: string, password: string, fullName?: string) => {
    const result = await apiPost<AuthResult>("/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    tokenManager.setTokens(result.tokens.access_token, result.tokens.refresh_token);
    setUser(result.user);
  }, []);

  const logout = useCallback(async () => {
    const refresh = tokenManager.getRefresh();
    if (refresh) {
      try {
        await apiPost("/auth/logout", { refresh_token: refresh });
      } catch {
        // best effort
      }
    }
    tokenManager.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
