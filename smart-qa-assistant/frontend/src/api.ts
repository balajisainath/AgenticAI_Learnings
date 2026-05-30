import type { AskRequest, AskResponse, CompareRequest, CompareResponse, GraphResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function askQuestion(payload: AskRequest): Promise<AskResponse> {
  return request<AskResponse>("/api/v1/chat/ask", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function comparePromptTechniques(payload: CompareRequest): Promise<CompareResponse> {
  return request<CompareResponse>("/api/v1/chat/compare", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchGraph(): Promise<GraphResponse> {
  return request<GraphResponse>("/api/v1/graph");
}
