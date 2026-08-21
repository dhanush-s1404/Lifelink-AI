export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    request_id?: string;
  };
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string;

  constructor(status: number, code: string, message: string, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

const ACCESS_TOKEN_KEY = "lifelink_access_token";
const REFRESH_TOKEN_KEY = "lifelink_refresh_token";

class TokenManager {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
      this.refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);
    }
  }

  getAccess(): string | null {
    return this.accessToken;
  }

  getRefresh(): string | null {
    return this.refreshToken;
  }

  setTokens(access: string, refresh: string): void {
    this.accessToken = access;
    this.refreshToken = refresh;
    sessionStorage.setItem(ACCESS_TOKEN_KEY, access);
    sessionStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }

  clear(): void {
    this.accessToken = null;
    this.refreshToken = null;
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  static clearAll(): void {
    if (typeof window === "undefined") return;
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

export const tokenManager = new TokenManager();

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

let refreshPromise: Promise<string | null> | null = null;

async function parseError(res: Response): Promise<ApiError> {
  let code = `HTTP_${res.status}`;
  let message = res.statusText || "Request failed";
  let requestId: string | undefined;

  try {
    const body = (await res.json()) as ApiErrorBody;
    if (body.error) {
      code = body.error.code ?? code;
      message = body.error.message ?? message;
      requestId = body.error.request_id;
    }
  } catch {
    // non-JSON error body
  }

  return new ApiError(res.status, code, message, requestId);
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenManager.getRefresh();
  if (!refresh) return null;

  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!res.ok) {
    tokenManager.clear();
    return null;
  }

  const data = (await res.json()) as { access_token: string; refresh_token: string };
  tokenManager.setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  _retry = true
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  const access = tokenManager.getAccess();
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (res.status === 401 && _retry) {
    const wasAuthEndpoint = path.startsWith("/auth/");
    if (!wasAuthEndpoint) {
      refreshPromise = refreshPromise ?? refreshAccessToken();
      const newAccess = await refreshPromise;
      refreshPromise = null;

      if (newAccess) {
        return apiFetch<T>(path, init, false);
      }
    }
  }

  if (!res.ok) {
    throw await parseError(res);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export function apiGet<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  if (!params) return apiFetch<T>(path);
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) search.set(key, String(value));
  }
  const qs = search.toString();
  return apiFetch<T>(qs ? `${path}?${qs}` : path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
}

export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined });
}

export function apiDelete<T = void>(path: string): Promise<T> {
  return apiFetch<T>(path, { method: "DELETE" });
}