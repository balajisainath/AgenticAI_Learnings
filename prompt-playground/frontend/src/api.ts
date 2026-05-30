import type { Prompt, PromptVersion, RunResult, CompareResponse, PromptStats, TestCase } from './types';

const BASE = '/api/v1';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// Prompts
export const api = {
  listPrompts: () => request<Prompt[]>('/prompts'),
  createPrompt: (data: { name: string; description: string }) =>
    request<Prompt>('/prompts', { method: 'POST', body: JSON.stringify(data) }),
  getPrompt: (id: string) => request<Prompt>(`/prompts/${id}`),
  updatePrompt: (id: string, data: { name?: string; description?: string }) =>
    request<Prompt>(`/prompts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePrompt: (id: string) =>
    request<{ status: string }>(`/prompts/${id}`, { method: 'DELETE' }),

  // Versions
  listVersions: (promptId: string) =>
    request<PromptVersion[]>(`/prompts/${promptId}/versions`),
  createVersion: (promptId: string, data: {
    system_prompt: string;
    user_prompt_template: string;
    model: string;
    temperature: number;
    notes: string;
  }) => request<PromptVersion>(`/prompts/${promptId}/versions`, { method: 'POST', body: JSON.stringify(data) }),

  // Test Cases
  listTestCases: (promptId: string) =>
    request<TestCase[]>(`/prompts/${promptId}/test-cases`),
  createTestCase: (promptId: string, data: { name: string; variables: Record<string, string> }) =>
    request<TestCase>(`/prompts/${promptId}/test-cases`, { method: 'POST', body: JSON.stringify(data) }),

  // Run
  runPrompt: (data: {
    version_id: string;
    input_text: string;
    variables?: Record<string, string>;
    model?: string;
    temperature?: number;
  }) => request<RunResult>('/run', { method: 'POST', body: JSON.stringify(data) }),

  rateRun: (runId: string, data: { rating: number; notes: string }) =>
    request<{ status: string }>(`/runs/${runId}/rate`, { method: 'PUT', body: JSON.stringify(data) }),

  getRunHistory: (versionId: string) =>
    request<RunResult[]>(`/runs/history/${versionId}`),

  // Compare
  compare: (data: {
    prompt_id: string;
    version_ids: string[];
    input_text: string;
    variables?: Record<string, string>;
    model?: string;
    temperature?: number;
  }) => request<CompareResponse>('/compare', { method: 'POST', body: JSON.stringify(data) }),

  // Stats
  getStats: (promptId: string) => request<PromptStats>(`/prompts/${promptId}/stats`),
};
