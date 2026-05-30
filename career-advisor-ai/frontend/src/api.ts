import type {
  CareerAnalysisRequest,
  CareerAnalysisResponse,
  ChatRequest,
  ChatResponse,
  DeepResearchRequest,
  DeepResearchResponse,
  GraphResponse,
} from "./types";

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

export function analyzeCareer(payload: CareerAnalysisRequest): Promise<CareerAnalysisResponse> {
  return request<CareerAnalysisResponse>("/api/v1/career/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function chatCareerCoach(payload: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/api/v1/career/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deepResearch(payload: DeepResearchRequest): Promise<DeepResearchResponse> {
  return request<DeepResearchResponse>("/api/v1/career/deep-research", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchGraph(): Promise<GraphResponse> {
  return request<GraphResponse>("/api/v1/career/graph");
}
