export interface Prompt {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  version_count: number;
  latest_version: number | null;
}

export interface PromptVersion {
  id: string;
  prompt_id: string;
  version_number: number;
  system_prompt: string;
  user_prompt_template: string;
  model: string;
  temperature: number;
  notes: string;
  created_at: string;
}

export interface TestCase {
  id: string;
  prompt_id: string;
  name: string;
  variables: Record<string, string>;
  created_at: string;
}

export interface RunResult {
  id: string;
  version_id: string;
  test_case_id: string | null;
  input_text: string;
  variables: Record<string, string>;
  output_text: string;
  model_used: string;
  temperature: number;
  latency_ms: number;
  token_count: number;
  rating: number;
  notes: string;
  created_at: string;
}

export interface CompareResult {
  version_id: string;
  version_number: number;
  output_text: string;
  latency_ms: number;
  token_count: number;
}

export interface CompareResponse {
  id: string;
  name: string;
  prompt_id: string;
  version_ids: string[];
  input_text: string;
  variables: Record<string, string>;
  results: CompareResult[];
  created_at: string;
}

export interface VersionStats {
  version_id: string;
  version_number: number;
  total_runs: number;
  avg_rating: number;
  avg_latency_ms: number;
  avg_tokens: number;
}

export interface PromptStats {
  prompt_id: string;
  prompt_name: string;
  versions: VersionStats[];
}
