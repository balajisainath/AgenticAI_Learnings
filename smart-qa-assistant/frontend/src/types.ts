export type Persona = "teacher" | "architect" | "analyst" | "product_coach";

export type PromptTechnique =
  | "auto"
  | "zero_shot"
  | "role"
  | "few_shot"
  | "chain_of_thought"
  | "step_back"
  | "critique_refine"
  | "self_consistency"
  | "style_variation";

export type PromptStyle = "concise" | "technical" | "socratic" | "executive";

export interface AskRequest {
  question: string;
  persona: Persona;
  style: PromptStyle;
  technique: PromptTechnique;
}

export interface CompareRequest {
  question: string;
  persona: Persona;
  style: PromptStyle;
  techniques: PromptTechnique[];
}

export interface TraceStep {
  node: string;
  detail: string;
}

export interface AskResponse {
  technique: PromptTechnique;
  answer: string;
  prompt_preview: string;
  trace: TraceStep[];
  metadata: Record<string, string>;
}

export interface CompareResponse {
  question: string;
  persona: Persona;
  style: PromptStyle;
  responses: AskResponse[];
}

export interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface GraphResponse {
  title: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
