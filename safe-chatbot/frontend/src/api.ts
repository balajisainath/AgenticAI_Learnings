import type { ChatRequest, ChatResponse } from './types';

const BASE = '/api/v1';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function sendMessage(payload: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat/message', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchHealth(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/health');
}
