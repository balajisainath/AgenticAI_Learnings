import { useEffect, useMemo, useState } from "react";

import { analyzeCareer, chatCareerCoach, deepResearch, fetchGraph } from "./api";
import { GraphFlow } from "./components/GraphFlow";
import "./App.css";
import type {
  CareerAnalysisResponse,
  CareerProfile,
  ChatResponse,
  DeepResearchResponse,
  GraphResponse,
  TraceStep,
} from "./types";

function splitCSV(input: string): string[] {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function getResearchMode(result: DeepResearchResponse): { label: string; tone: string; detail: string } {
  const mode = result.metadata?.mode;
  const status = result.metadata?.status ?? "";

  if (mode === "tavily-live") {
    return { label: "Live Tavily", tone: "live", detail: "Web results are being used." };
  }
  if (mode === "deep-agent") {
    return { label: "Deep Agent", tone: "agent", detail: "Deep multi-agent research is active." };
  }
  if (mode === "local-fallback" || !result.used_deep_agent) {
    return {
      label: "Local Fallback",
      tone: "fallback",
      detail: status || "Using local knowledge base due to unavailable deep research runtime.",
    };
  }

  return { label: "Unknown Mode", tone: "unknown", detail: status || "No mode metadata returned." };
}

function App() {
  const [sessionId, setSessionId] = useState(`session-${Math.floor(Date.now() / 1000)}`);

  const [fullName, setFullName] = useState("Demo User");
  const [currentRole, setCurrentRole] = useState("Student");
  const [yearsExperience, setYearsExperience] = useState("0");
  const [education, setEducation] = useState("Bachelor's Degree");
  const [skills, setSkills] = useState("python, sql");
  const [interests, setInterests] = useState("career growth, AI applications");
  const [targetRoles, setTargetRoles] = useState("Machine Learning Engineer");
  const [preferredLocations, setPreferredLocations] = useState("Remote");
  const [priorities, setPriorities] = useState("career growth, skill development");
  const [resumeText, setResumeText] = useState("");

  const [chatMessage, setChatMessage] = useState(
    "Give me a 2-week interview prep plan for entry-level machine learning roles.",
  );
  const [deepResearchQuery, setDeepResearchQuery] = useState(
    "What are current hiring trends for entry-level machine learning roles in remote markets?",
  );

  const [analysis, setAnalysis] = useState<CareerAnalysisResponse | null>(null);
  const [chatResult, setChatResult] = useState<ChatResponse | null>(null);
  const [deepResearchResult, setDeepResearchResult] = useState<DeepResearchResponse | null>(null);

  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [activeTrace, setActiveTrace] = useState<TraceStep[]>([]);

  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [loadingDeepResearch, setLoadingDeepResearch] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetchGraph()
      .then((payload) => setGraph(payload))
      .catch(() => {
        setError("Could not load workflow graph. Ensure the backend is running.");
      });
  }, []);

  const profilePreview = useMemo<CareerProfile>(
    () => ({
      full_name: fullName,
      current_role: currentRole,
      years_experience: Number(yearsExperience),
      education,
      skills: splitCSV(skills),
      interests: splitCSV(interests),
      target_roles: splitCSV(targetRoles),
      preferred_locations: splitCSV(preferredLocations),
    }),
    [
      currentRole,
      education,
      fullName,
      interests,
      preferredLocations,
      skills,
      targetRoles,
      yearsExperience,
    ],
  );

  async function handleAnalyzeCareer(): Promise<void> {
    setLoadingAnalysis(true);
    setError("");
    setActiveTrace([]);

    try {
      const response = await analyzeCareer({
        session_id: sessionId,
        profile: profilePreview,
        resume_text: resumeText,
        priorities: splitCSV(priorities),
      });

      setAnalysis(response);
      setSessionId(response.session_id);
      setActiveTrace(response.trace);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Request failed.";
      setError(message);
    } finally {
      setLoadingAnalysis(false);
    }
  }

  async function handleChat(): Promise<void> {
    setLoadingChat(true);
    setError("");
    setActiveTrace([]);

    try {
      const response = await chatCareerCoach({
        session_id: sessionId,
        message: chatMessage,
        profile: profilePreview,
      });

      setChatResult(response);
      setActiveTrace(response.trace);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Request failed.";
      setError(message);
    } finally {
      setLoadingChat(false);
    }
  }

  async function handleDeepResearch(): Promise<void> {
    setLoadingDeepResearch(true);
    setError("");

    try {
      const response = await deepResearch({ query: deepResearchQuery, session_id: sessionId });
      setDeepResearchResult(response);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Request failed.";
      setError(message);
    } finally {
      setLoadingDeepResearch(false);
    }
  }

  return (
    <div className="page-shell">
      <header className="hero-panel">
        <p className="hero-kicker">LangGraph Multi-Agent Project</p>
        <h1>Career Advisor AI</h1>
        <p>
          Analyze profiles, recommend career paths, match jobs, highlight skill gaps, generate
          roadmap phases, review resume quality, and run optional Deep Agents research.
        </p>
      </header>

      <section className="layout-grid">
        <aside className="control-panel">
          <header className="panel-header">
            <h2>Profile Input</h2>
            <p>Complete the form once, then run analysis, chat, and deep research.</p>
          </header>

          <section className="input-section">
            <h3>Session + Basics</h3>
            <div className="section-grid">
              <div className="field-group wide">
                <label htmlFor="session">Session ID</label>
                <input
                  id="session"
                  value={sessionId}
                  onChange={(event) => setSessionId(event.target.value)}
                  placeholder="Auto-generated session id"
                />
              </div>

              <div className="field-group wide">
                <label htmlFor="fullName">Name</label>
                <input
                  id="fullName"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Your name"
                />
              </div>

              <div className="field-group">
                <label htmlFor="role">Current Role</label>
                <input
                  id="role"
                  value={currentRole}
                  onChange={(event) => setCurrentRole(event.target.value)}
                  placeholder="Student / Developer / Analyst"
                />
              </div>

              <div className="field-group">
                <label htmlFor="years">Years Experience</label>
                <input
                  id="years"
                  type="number"
                  min={0}
                  max={40}
                  step={0.5}
                  value={yearsExperience}
                  onChange={(event) => setYearsExperience(event.target.value)}
                />
              </div>

              <div className="field-group wide">
                <label htmlFor="education">Education</label>
                <input
                  id="education"
                  value={education}
                  onChange={(event) => setEducation(event.target.value)}
                  placeholder="Degree, certification, or equivalent"
                />
              </div>
            </div>
          </section>

          <section className="input-section">
            <h3>Career Signals</h3>
            <div className="field-group">
              <label htmlFor="skills">Skills (comma-separated)</label>
              <textarea
                id="skills"
                value={skills}
                onChange={(event) => setSkills(event.target.value)}
                rows={4}
                placeholder="python, fastapi, sql, data analysis"
              />
            </div>

            <div className="field-group">
              <label htmlFor="interests">Interests (comma-separated)</label>
              <textarea
                id="interests"
                value={interests}
                onChange={(event) => setInterests(event.target.value)}
                rows={3}
                placeholder="AI products, data science, backend engineering"
              />
            </div>

            <div className="field-group">
              <label htmlFor="targets">Target Roles (comma-separated)</label>
              <textarea
                id="targets"
                value={targetRoles}
                onChange={(event) => setTargetRoles(event.target.value)}
                rows={3}
                placeholder="Machine Learning Engineer, Data Scientist"
              />
            </div>

            <div className="section-grid">
              <div className="field-group wide">
                <label htmlFor="locations">Preferred Locations</label>
                <input
                  id="locations"
                  value={preferredLocations}
                  onChange={(event) => setPreferredLocations(event.target.value)}
                  placeholder="Remote, Bengaluru, Hyderabad"
                />
              </div>

              <div className="field-group wide">
                <label htmlFor="priorities">Priorities</label>
                <input
                  id="priorities"
                  value={priorities}
                  onChange={(event) => setPriorities(event.target.value)}
                  placeholder="growth, compensation, flexibility"
                />
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="resume">Resume Text (optional)</label>
              <textarea
                id="resume"
                value={resumeText}
                onChange={(event) => setResumeText(event.target.value)}
                rows={8}
                placeholder="Paste resume text for keyword and impact analysis"
              />
            </div>

            <button
              type="button"
              onClick={handleAnalyzeCareer}
              disabled={loadingAnalysis || profilePreview.current_role.trim().length < 2}
            >
              {loadingAnalysis ? "Analyzing Career Profile..." : "Analyze Career"}
            </button>
          </section>

          <section className="input-section">
            <h3>Interactive Agents</h3>

            <div className="field-group">
              <label htmlFor="chatQuestion">Career Coach Chat</label>
              <textarea
                id="chatQuestion"
                value={chatMessage}
                onChange={(event) => setChatMessage(event.target.value)}
                rows={4}
                placeholder="Ask for interview prep, role transition plan, or project guidance"
              />
              <button
                type="button"
                className="secondary"
                onClick={handleChat}
                disabled={loadingChat || chatMessage.trim().length < 4}
              >
                {loadingChat ? "Generating Chat Guidance..." : "Ask Career Coach"}
              </button>
            </div>

            <div className="field-group">
              <label htmlFor="deepResearch">Deep Agents Research</label>
              <textarea
                id="deepResearch"
                value={deepResearchQuery}
                onChange={(event) => setDeepResearchQuery(event.target.value)}
                rows={4}
                placeholder="Ask market trend questions for role/location"
              />
              <button
                type="button"
                className="ghost"
                onClick={handleDeepResearch}
                disabled={loadingDeepResearch || deepResearchQuery.trim().length < 4}
              >
                {loadingDeepResearch ? "Running Deep Research..." : "Run Deep Research"}
              </button>
            </div>
          </section>

          {error && <p className="error">{error}</p>}
        </aside>

        <section className="results-panel">
          <header>
            <h2>Analysis Output</h2>
            <p>Production-style career intelligence output powered by LangGraph role agents.</p>
          </header>

          {!analysis && !loadingAnalysis && (
            <div className="empty-state">
              Submit profile input to generate recommendations, job matches, roadmap, and safety
              report.
            </div>
          )}

          {analysis && (
            <>
              <section className="result-section">
                <h3>Runtime Signals</h3>
                <div className="result-grid">
                  <article className="mini-card">
                    <h4>Model</h4>
                    <p>{analysis.metadata.model || "unknown"}</p>
                    <p>Provider: {analysis.metadata.provider || "unknown"}</p>
                  </article>
                  <article className="mini-card">
                    <h4>Data Source</h4>
                    <p>
                      Job matching: {analysis.metadata.job_data_source === "tavily-live" ? "Live Web" : "Local KB"}
                    </p>
                    <p>Recommendations: {analysis.metadata.recommendation_mode || "default"}</p>
                  </article>
                </div>
              </section>

              <section className="result-section">
                <h3>Profile Summary</h3>
                <p>{analysis.profile_summary}</p>
              </section>

              <section className="result-section">
                <h3>Career Recommendations</h3>
                <div className="result-grid">
                  {analysis.career_recommendations.map((item) => (
                    <article key={item.role} className="mini-card">
                      <h4>{item.role}</h4>
                      <p>
                        Confidence: <strong>{Math.round(item.confidence_score * 100)}%</strong>
                      </p>
                      <p>{item.market_outlook}</p>
                      <p>{item.rationale[0]}</p>
                      <p>Matching: {item.matching_skills.join(", ") || "None"}</p>
                      <p>Missing: {item.missing_skills.join(", ") || "None"}</p>
                    </article>
                  ))}
                </div>
              </section>

              <section className="result-section">
                <h3>Job Matches</h3>
                <div className="result-grid">
                  {analysis.job_matches.map((item) => (
                    <article key={item.job_id} className="mini-card">
                      <h4>{item.title}</h4>
                      <p>
                        {item.company} | {item.location}
                      </p>
                      <p>
                        Source: <strong>{item.source === "tavily-live" ? "Live Web" : "Local Sample KB"}</strong>
                      </p>
                      <p>
                        Match Score: <strong>{Math.round(item.match_score * 100)}%</strong>
                      </p>
                      {item.job_url && (
                        <p>
                          <a href={item.job_url} target="_blank" rel="noreferrer">
                            Open listing
                          </a>
                        </p>
                      )}
                      <p>Missing: {item.missing_skills.join(", ") || "None"}</p>
                    </article>
                  ))}
                </div>
              </section>

              <section className="result-section">
                <h3>Skill Gaps + Roadmap</h3>
                <div className="result-grid">
                  <article className="mini-card">
                    <h4>Top Skill Gaps</h4>
                    <ul>
                      {analysis.skill_gaps.map((gap) => (
                        <li key={gap.skill}>
                          {gap.skill} ({gap.priority})
                        </li>
                      ))}
                    </ul>
                  </article>
                  <article className="mini-card">
                    <h4>Roadmap Phases</h4>
                    <ul>
                      {analysis.roadmap.map((step) => (
                        <li key={step.phase}>
                          {step.phase} ({step.duration_weeks} weeks)
                        </li>
                      ))}
                    </ul>
                  </article>
                </div>
              </section>

              <section className="result-section">
                <h3>Resume + Safety</h3>
                <div className="result-grid">
                  <article className="mini-card">
                    <h4>Resume Score</h4>
                    <p>
                      <strong>{Math.round(analysis.resume_analysis.overall_score * 100)}%</strong>
                    </p>
                    <p>{analysis.resume_analysis.rewritten_summary}</p>
                  </article>
                  <article className="mini-card">
                    <h4>Safety Report</h4>
                    <p>Risk: {analysis.safety_report.overall_risk}</p>
                    <p>{analysis.safety_report.flags[0] ?? "No safety flags."}</p>
                  </article>
                </div>
              </section>

              <section className="result-section">
                <h3>Retrieved Context</h3>
                <div className="result-grid">
                  {analysis.retrieved_context.map((doc) => (
                    <article key={doc.id} className="mini-card">
                      <h4>{doc.title}</h4>
                      <p>{doc.category}</p>
                      <a href={doc.url} target="_blank" rel="noreferrer">
                        Source
                      </a>
                    </article>
                  ))}
                </div>
              </section>

              <button type="button" className="ghost" onClick={() => setActiveTrace(analysis.trace)}>
                Replay Analysis Trace In Graph
              </button>
            </>
          )}

          {chatResult && (
            <section className="result-section">
              <h3>Career Coach Chat</h3>
              <article className="mini-card">
                <p className="prelike">{chatResult.answer}</p>
                <p>Risk: {chatResult.safety_report.overall_risk}</p>
                <button type="button" className="ghost" onClick={() => setActiveTrace(chatResult.trace)}>
                  Replay Chat Trace In Graph
                </button>
              </article>
            </section>
          )}

          {deepResearchResult && (
            <section className="result-section">
              <h3>Deep Research</h3>
              <article className="mini-card">
                <div className="mode-row">
                  <span className={`mode-badge ${getResearchMode(deepResearchResult).tone}`}>
                    {getResearchMode(deepResearchResult).label}
                  </span>
                  <span className="mode-detail">{getResearchMode(deepResearchResult).detail}</span>
                </div>
                <p className="prelike">{deepResearchResult.summary}</p>
                {deepResearchResult.sources.length > 0 && (
                  <ul>
                    {deepResearchResult.sources.map((source, idx) => (
                      <li key={`${source}-${idx}`}>{source}</li>
                    ))}
                  </ul>
                )}
              </article>
            </section>
          )}
        </section>
      </section>

      <GraphFlow graph={graph} trace={activeTrace} />
    </div>
  );
}

export default App;
