// Authentication utilities for frontend

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Token storage keys
const ACCESS_TOKEN_KEY = 'ai_agent_access_token';
const REFRESH_TOKEN_KEY = 'ai_agent_refresh_token';
const USER_KEY = 'ai_agent_user';

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
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const tokens = await response.json();
  setTokens(tokens);
  return tokens;
}

export async function register(data: RegisterData): Promise<User> {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

export async function refreshAccessToken(): Promise<AuthTokens | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await fetch(`${API_BASE}/api/auth/refresh`, {
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
    const response = await fetch(`${API_BASE}/api/auth/me`, {
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
  const response = await fetch(`${API_BASE}/api/auth/api-keys`, {
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
  const response = await fetch(`${API_BASE}/api/auth/api-keys`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to list API keys');
  }

  return response.json();
}

export async function revokeAPIKey(keyId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/auth/api-keys/${keyId}`, {
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
  const response = await fetch(`${API_BASE}/api/auth/usage`, {
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
