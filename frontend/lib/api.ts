import { ChatResponse, Settings } from './types';
import { getAccessToken, refreshAccessToken, clearTokens } from './auth';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to get auth headers
function getAuthHeaders(): HeadersInit {
  const token = getAccessToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// Helper for authenticated fetch with auto-refresh
async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = { ...getAuthHeaders(), ...options.headers };
  let response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    const newTokens = await refreshAccessToken();
    if (newTokens) {
      const retryHeaders = { ...getAuthHeaders(), ...options.headers };
      response = await fetch(url, { ...options, headers: retryHeaders });
    } else {
      clearTokens();
      if (typeof window !== 'undefined') window.location.href = '/login';
    }
  }

  return response;
}

// Chat API
export async function sendMessage(message: string): Promise<ChatResponse> {
  const response = await authFetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
  if (!response.ok) throw new Error((await response.json()).detail || 'Failed to send message');
  return response.json();
}

export async function clearChat(): Promise<void> {
  await authFetch(`${API_BASE}/api/chat/clear`, { method: 'POST' });
}

export async function getHistory(): Promise<{ history: any[] }> {
  const response = await authFetch(`${API_BASE}/api/chat/history`);
  return response.json();
}

// Settings API
export async function getSettings(): Promise<Settings> {
  const response = await authFetch(`${API_BASE}/api/settings`);
  return response.json();
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  const response = await authFetch(`${API_BASE}/api/settings`, {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
  return response.json();
}

export async function getInfo(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/info`);
  return response.json();
}

// Memory API
export async function searchMemory(query: string, limit: number = 5): Promise<any> {
  const url = `${API_BASE}/api/memory/search?query=${encodeURIComponent(query)}&limit=${limit}`;
  const response = await authFetch(url);
  return response.json();
}

export async function getMemoryStats(): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/memory/stats`);
  return response.json();
}

// Knowledge Base API
export async function searchKnowledge(query: string, category?: string): Promise<any> {
  const url = new URL(`${API_BASE}/api/knowledge/search`);
  url.searchParams.set('query', query);
  if (category) url.searchParams.set('category', category);
  const response = await authFetch(url.toString());
  return response.json();
}

export async function addKnowledge(title: string, content: string, category: string = 'general'): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/knowledge`, {
    method: 'POST',
    body: JSON.stringify({ title, content, category }),
  });
  return response.json();
}

// Workflow API
export async function listWorkflows(search?: string, tags?: string): Promise<any> {
  const url = new URL(`${API_BASE}/api/workflows`);
  if (search) url.searchParams.set('search', search);
  if (tags) url.searchParams.set('tags', tags);
  const response = await authFetch(url.toString());
  return response.json();
}

export async function getWorkflow(id: string): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/workflows/${id}`);
  return response.json();
}

export async function createWorkflow(workflow: any): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/workflows`, {
    method: 'POST',
    body: JSON.stringify(workflow),
  });
  return response.json();
}

export async function runWorkflow(id: string, variables: any = {}): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/workflows/${id}/run`, {
    method: 'POST',
    body: JSON.stringify(variables),
  });
  return response.json();
}

export async function deleteWorkflow(id: string): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/workflows/${id}`, { method: 'DELETE' });
  return response.json();
}

export async function getWorkflowTemplates(): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/workflows/templates`);
  return response.json();
}

// Scheduling API
export async function listScheduledTasks(): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/schedule`);
  return response.json();
}

export async function scheduleWorkflow(task: any): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/schedule`, {
    method: 'POST',
    body: JSON.stringify(task),
  });
  return response.json();
}

export async function pauseTask(taskId: string): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/schedule/${taskId}/pause`, { method: 'POST' });
  return response.json();
}

export async function resumeTask(taskId: string): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/schedule/${taskId}/resume`, { method: 'POST' });
  return response.json();
}

export async function cancelTask(taskId: string): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/schedule/${taskId}`, { method: 'DELETE' });
  return response.json();
}

// Tools API
export async function listTools(): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/tools`);
  return response.json();
}

export async function executeTool(toolName: string, params: any): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/tools/${toolName}/execute`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
  return response.json();
}

// Files API
export async function listFiles(path: string = '.'): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/files?path=${encodeURIComponent(path)}`);
  return response.json();
}

export async function readFile(path: string): Promise<any> {
  const response = await authFetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(path)}`);
  return response.json();
}

// Health Check (no auth needed)
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// WebSocket
export function createWebSocket(): WebSocket {
  const wsUrl = API_BASE.replace('http', 'ws') + '/ws';
  return new WebSocket(wsUrl);
}
