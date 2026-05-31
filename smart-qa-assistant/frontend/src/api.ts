import type { AskRequest, AskResponse, CompareRequest, CompareResponse, GraphResponse, StreamEvent } from "./types";

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

export function streamAsk(
  payload: AskRequest,
  onEvent: (event: StreamEvent) => void,
  onError: (error: string) => void,
  onDone: () => void,
): AbortController {
  const controller = new AbortController();

  fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text();
        onError(text || `Stream failed: ${response.status}`);
        return;
      }
      const reader = response.body?.getReader();
      if (!reader) {
        onError("No response body");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const json = line.slice(6).trim();
            if (json) {
              try {
                const event = JSON.parse(json) as StreamEvent;
                onEvent(event);
              } catch {
                // skip malformed
              }
            }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError(err.message ?? "Stream connection failed");
      }
    });

  return controller;
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
