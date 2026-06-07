export interface CareerProfile {
  full_name?: string;
  current_role: string;
  years_experience: number;
  education: string;
  skills: string[];
  interests: string[];
  target_roles: string[];
  preferred_locations: string[];
}

export interface CareerAnalysisRequest {
  session_id?: string;
  profile: CareerProfile;
  resume_text?: string;
  priorities: string[];
}

export interface ChatRequest {
  session_id: string;
  message: string;
  profile?: CareerProfile;
}

export interface DeepResearchRequest {
  query: string;
  session_id?: string;
}

export interface TraceStep {
  node: string;
  detail: string;
}

export interface RetrievedItem {
  id: string;
  title: string;
  category: string;
  url: string;
  score: number;
  snippet: string;
}

export interface CareerRecommendation {
  role: string;
  confidence_score: number;
  rationale: string[];
  market_outlook: string;
  matching_skills: string[];
  missing_skills: string[];
}

export interface JobMatch {
  job_id: string;
  title: string;
  company: string;
  location: string;
  match_score: number;
  rationale: string[];
  missing_skills: string[];
  job_url?: string | null;
  source: string;
}

export interface SkillGap {
  skill: string;
  priority: string;
  why_important: string;
  suggested_resources: string[];
}

export interface RoadmapStep {
  phase: string;
  duration_weeks: number;
  goals: string[];
  actions: string[];
  resources: string[];
}

export interface ResumeIssue {
  issue: string;
  severity: string;
  suggestion: string;
}

export interface ResumeAnalysis {
  overall_score: number;
  strengths: string[];
  issues: ResumeIssue[];
  rewritten_summary: string;
}

export interface SafetyReport {
  overall_risk: string;
  flags: string[];
  bias_checks: string[];
  transparency_notes: string[];
}

export interface CareerAnalysisResponse {
  session_id: string;
  profile_summary: string;
  career_recommendations: CareerRecommendation[];
  job_matches: JobMatch[];
  skill_gaps: SkillGap[];
  roadmap: RoadmapStep[];
  resume_analysis: ResumeAnalysis;
  safety_report: SafetyReport;
  retrieved_context: RetrievedItem[];
  memory_notes: string[];
  trace: TraceStep[];
  metadata: Record<string, string>;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  safety_report: SafetyReport;
  trace: TraceStep[];
  metadata: Record<string, string>;
}

export interface DeepResearchResponse {
  summary: string;
  sources: string[];
  used_deep_agent: boolean;
  metadata: Record<string, string>;
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
