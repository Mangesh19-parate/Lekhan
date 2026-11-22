import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiClient, setMemoryCsrfToken } from "../api";

export interface UserProfile {
  id: string;
  tenant_id: string;
  email: string;
  display_name: string;
  role: string;
  ui_language: string;
}

interface AuthContextType {
  user: UserProfile | null;
  csrfToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ mfaRequired: boolean }>;
  verifyMfaLogin: (code?: string, recoveryCode?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  csrfToken: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => ({ mfaRequired: false }),
  verifyMfaLogin: async () => {},
  logout: async () => {},
  refreshUser: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check current session on mount via GET /api/v1/auth/me
  const refreshUser = useCallback(async () => {
    try {
      const data = await apiClient<{ user: UserProfile; csrf_token: string }>("/api/v1/auth/me");
      setUser(data.user);
      setCsrfToken(data.csrf_token);
      setMemoryCsrfToken(data.csrf_token);
    } catch {
      setUser(null);
      setCsrfToken(null);
      setMemoryCsrfToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string): Promise<{ mfaRequired: boolean }> => {
    const data = await apiClient<{ user: UserProfile; csrf_token: string; mfa_required?: boolean }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setCsrfToken(data.csrf_token);
    setMemoryCsrfToken(data.csrf_token);
    if (!data.mfa_required) {
      setUser(data.user);
      return { mfaRequired: false };
    }
    return { mfaRequired: true };
  };

  const verifyMfaLogin = async (code?: string, recoveryCode?: string): Promise<void> => {
    const res = await apiClient<{ status: string; verified: boolean; message?: string }>("/api/v1/auth/mfa/verify", {
      method: "POST",
      body: JSON.stringify({ code: code || undefined, recovery_code: recoveryCode || undefined }),
    });
    if (res.verified) {
      await refreshUser();
    }
  };

  const logout = async () => {
    try {
      await apiClient("/api/v1/auth/logout", {
        method: "POST",
        headers: csrfToken ? { "X-CSRF-Token": csrfToken } : undefined,
      });
    } finally {
      setUser(null);
      setCsrfToken(null);
      setMemoryCsrfToken(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        csrfToken,
        isAuthenticated: !!user,
        isLoading,
        login,
        verifyMfaLogin,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
