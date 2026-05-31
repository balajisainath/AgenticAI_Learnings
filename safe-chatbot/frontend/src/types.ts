export type Provider = 'openai' | 'anthropic' | 'google_genai';

export interface HistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id: string;
  history: HistoryMessage[];
  provider: Provider;
  guardrails_ai_enabled: boolean;
  nemo_enabled: boolean;
}

export interface GuardrailsAIInfo {
  active: boolean;
  input_passed: boolean;
  input_blocked: boolean;
  output_passed: boolean;
  output_filtered: boolean;
  failed_validators: string[];
  error_message: string | null;
}

export interface NemoInfo {
  active: boolean;
  input_checked: boolean;
  input_blocked: boolean;
  output_checked: boolean;
  rails_triggered: string[];
  block_reason: string | null;
}

export interface GuardrailsInfo {
  input_blocked: boolean;
  output_filtered: boolean;
  block_reason: string | null;
  guardrails_ai: GuardrailsAIInfo;
  nemo: NemoInfo;
}

export interface TraceStep {
  node: string;
  detail: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  guardrails: GuardrailsInfo;
  trace: TraceStep[];
  metadata: Record<string, string>;
}

// ── Local UI types ────────────────────────────────────────────────────────────

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  guardrails?: GuardrailsInfo;
  trace?: TraceStep[];
  metadata?: Record<string, string>;
  timestamp: Date;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  provider: Provider;
}
