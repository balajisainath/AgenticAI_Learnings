import { useCallback, useEffect, useRef, useState } from "react";

import { streamAsk, comparePromptTechniques, fetchGraph } from "./api";
import { GraphFlow } from "./components/GraphFlow";
import { ResponseCard } from "./components/ResponseCard";
import "./App.css";
import type {
  AskResponse,
  Persona,
  PromptStyle,
  PromptTechnique,
  StreamEvent,
  GraphResponse,
} from "./types";

const PERSONAS: Persona[] = ["teacher", "architect", "analyst", "product_coach"];
const STYLES: PromptStyle[] = ["technical", "concise", "socratic", "executive"];
const TECHNIQUES: PromptTechnique[] = [
  "auto",
  "zero_shot",
  "role",
  "few_shot",
  "chain_of_thought",
  "step_back",
  "critique_refine",
  "self_consistency",
  "style_variation",
];

function titleCase(value: string): string {
  return value
    .split("_")
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(" ");
}

function App() {
  const [question, setQuestion] = useState("");
  const [persona, setPersona] = useState<Persona>("architect");
  const [style, setStyle] = useState<PromptStyle>("technical");
  const [technique, setTechnique] = useState<PromptTechnique>("auto");

  const [responses, setResponses] = useState<AskResponse[]>([]);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [activeNodes, setActiveNodes] = useState<string[]>([]);
  const [streamLog, setStreamLog] = useState<StreamEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchGraph().then(setGraph).catch(() => setError("Backend not reachable"));
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handleStream = useCallback(() => {
    if (!question.trim()) return;

    setLoading(true);
    setError("");
    setResponses([]);
    setActiveNodes([]);
    setStreamLog([]);

    abortRef.current?.abort();

    const controller = streamAsk(
      { question, persona, style, technique },
      (event: StreamEvent) => {
        setStreamLog((prev) => [...prev, event]);
        setActiveNodes((prev) => {
          if (!prev.includes(event.node)) return [...prev, event.node];
          return prev;
        });

        if (event.type === "complete" && event.result) {
          setResponses([event.result]);
          setLoading(false);
        }
      },
      (errMsg) => {
        setError(errMsg);
        setLoading(false);
      },
      () => {
        setLoading(false);
      },
    );

    abortRef.current = controller;
  }, [question, persona, style, technique]);

  const handleCompare = useCallback(async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError("");
    setActiveNodes([]);
    setStreamLog([]);
    abortRef.current?.abort();

    try {
      const result = await comparePromptTechniques({
        question,
        persona,
        style,
        techniques: ["role", "few_shot", "chain_of_thought", "style_variation"],
      });
      setResponses(result.responses);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }, [question, persona, style]);

  const streamState = loading
    ? "Streaming live execution"
    : streamLog.length > 0
      ? "Latest run completed"
      : "Idle";

  return (
    <div className="shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">Q</div>
          <span>Smart QA</span>
        </div>

        <div className="sidebar-section">
          <label>Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask something..."
            rows={4}
          />
        </div>

        <div className="sidebar-row">
          <div className="sidebar-section">
            <label>Persona</label>
            <select value={persona} onChange={(e) => setPersona(e.target.value as Persona)}>
              {PERSONAS.map((p) => (
                <option key={p} value={p}>{titleCase(p)}</option>
              ))}
            </select>
          </div>
          <div className="sidebar-section">
            <label>Style</label>
            <select value={style} onChange={(e) => setStyle(e.target.value as PromptStyle)}>
              {STYLES.map((s) => (
                <option key={s} value={s}>{titleCase(s)}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="sidebar-section">
          <label>Technique</label>
          <select value={technique} onChange={(e) => setTechnique(e.target.value as PromptTechnique)}>
            {TECHNIQUES.map((t) => (
              <option key={t} value={t}>{titleCase(t)}</option>
            ))}
          </select>
        </div>

        <div className="sidebar-actions">
          <button className="btn-primary" onClick={handleStream} disabled={loading || !question.trim()}>
            {loading ? "Running..." : "Run"}
          </button>
          <button className="btn-secondary" onClick={handleCompare} disabled={loading || !question.trim()}>
            Compare
          </button>
        </div>

        {error && <p className="error-msg">{error}</p>}
      </aside>

      {/* Main */}
      <main className="main-area">
        <section className="hero-strip">
          <div>
            <p className="hero-kicker">Prompt Engineering Lab</p>
            <h1>Smart Q&A Assistant</h1>
            <p className="hero-subtext">
              Live LangGraph node execution with side-by-side prompt strategy comparisons.
            </p>
          </div>
          <div className="hero-meta">
            <span className="meta-pill">{streamState}</span>
            <span className="meta-pill">Responses: {responses.length}</span>
          </div>
        </section>

        {/* Graph execution visualizer */}
        <GraphFlow graph={graph} activeNodes={activeNodes} streamLog={streamLog} />

        {/* Response cards */}
        <section className="responses-section">
          {responses.length === 0 && !loading && (
            <div className="empty">Enter a question and hit Run to see the LangGraph pipeline execute live.</div>
          )}
          <div className="response-grid">
            {responses.map((r, i) => (
              <ResponseCard key={`${r.technique}-${i}`} response={r} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
