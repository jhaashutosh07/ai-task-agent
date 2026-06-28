// Authentication utilities for frontend

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Token storage keys
const ACCESS_TOKEN_KEY = 'ai_agent_access_token';
const REFRESH_TOKEN_KEY = 'ai_agent_refresh_token';
const USER_KEY = 'ai_agent_user';

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// The backend runs on a free tier that spins down when idle. The first request
// after a while can return 502/503 (or briefly refuse the connection) while it
// wakes up. Retry transient failures with backoff so sign-in succeeds instead
// of failing on a cold start. `onRetry` lets the UI show a "waking up" message.
let authWakeListener: (() => void) | null = null;
export function onAuthWaking(cb: (() => void) | null): void {
  authWakeListener = cb;
}

async function resilientFetch(url: string, opts: RequestInit, retries = 6): Promise<Response> {
  let lastErr: any;
  for (let i = 0; i <= retries; i++) {
    try {
      const r = await fetch(url, opts);
      if ([502, 503, 504].includes(r.status) && i < retries) {
        authWakeListener?.();
        await sleep(4000 + i * 2000);
        continue;
      }
      return r;
    } catch (e) {
      lastErr = e;
      if (i < retries) { authWakeListener?.(); await sleep(4000 + i * 2000); continue; }
      throw e;
    }
  }
  throw lastErr;
}

async function parseError(r: Response, fallback: string): Promise<string> {
  try { const j = await r.json(); return j.detail || fallback; }
  catch { return `Server is starting up — please try again in a moment (HTTP ${r.status}).`; }
}

// Types
export interface User {
  id: string;
  email: string;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  usage_quota: number;
  usage_today: number;
  total_usage: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface APIKey {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used: string | null;
}

// Token management
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(tokens: AuthTokens): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userJson = localStorage.getItem(USER_KEY);
  if (userJson) {
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  }
  return null;
}

export function setStoredUser(user: User): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// Auth headers helper
export function getAuthHeaders(): HeadersInit {
  const token = getAccessToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// API calls
export async function login(credentials: LoginCredentials): Promise<AuthTokens> {
  let response: Response;
  try {
    response = await resilientFetch(`${API_BASE}${API_PREFIX}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
  } catch {
    throw new Error('Could not reach the server. Please check your connection and try again.');
  }

  if (!response.ok) {
    throw new Error(await parseError(response, 'Login failed'));
  }

  const tokens = await response.json();
  setTokens(tokens);
  return tokens;
}

export async function register(data: RegisterData): Promise<User> {
  let response: Response;
  try {
    response = await resilientFetch(`${API_BASE}${API_PREFIX}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  } catch {
    throw new Error('Could not reach the server. Please check your connection and try again.');
  }

  if (!response.ok) {
    throw new Error(await parseError(response, 'Registration failed'));
  }

  return response.json();
}

export async function refreshAccessToken(): Promise<AuthTokens | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await fetch(`${API_BASE}${API_PREFIX}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearTokens();
      return null;
    }

    const tokens = await response.json();
    setTokens(tokens);
    return tokens;
  } catch {
    clearTokens();
    return null;
  }
}

export async function getCurrentUser(): Promise<User | null> {
  const token = getAccessToken();
  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE}${API_PREFIX}/auth/me`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Try to refresh token
        const newTokens = await refreshAccessToken();
        if (newTokens) {
          return getCurrentUser();
        }
        clearTokens();
      }
      return null;
    }

    const user = await response.json();
    setStoredUser(user);
    return user;
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  clearTokens();
}

// API Key management
export async function createAPIKey(name: string): Promise<{ key: string; id: string }> {
  const response = await fetch(`${API_BASE}${API_PREFIX}/auth/api-keys`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create API key');
  }

  return response.json();
}

export async function listAPIKeys(): Promise<APIKey[]> {
  const response = await fetch(`${API_BASE}${API_PREFIX}/auth/api-keys`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to list API keys');
  }

  return response.json();
}

export async function revokeAPIKey(keyId: string): Promise<void> {
  const response = await fetch(`${API_BASE}${API_PREFIX}/auth/api-keys/${keyId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to revoke API key');
  }
}

// Usage stats
export async function getUsageStats(): Promise<{
  tokens_used_today: number;
  tokens_quota: number;
  total_tokens_used: number;
}> {
  const response = await fetch(`${API_BASE}${API_PREFIX}/auth/usage`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to get usage stats');
  }

  return response.json();
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

// Aliases for different naming conventions
export const listApiKeys = listAPIKeys;
export const createApiKey = createAPIKey;
export const revokeApiKey = revokeAPIKey;
