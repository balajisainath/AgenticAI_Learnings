import { useEffect, useMemo, useState } from "react";

import { askQuestion, comparePromptTechniques, fetchGraph } from "./api";
import { GraphFlow } from "./components/GraphFlow";
import { ResponseCard } from "./components/ResponseCard";
import "./App.css";
import type {
  AskResponse,
  Persona,
  PromptStyle,
  PromptTechnique,
  TraceStep,
  GraphResponse,
} from "./types";

const PERSONAS: Persona[] = ["teacher", "architect", "analyst", "product_coach"];
const PROMPT_STYLES: PromptStyle[] = ["technical", "concise", "socratic", "executive"];
const TECHNIQUES: PromptTechnique[] = [
  "auto",
  "role",
  "few_shot",
  "chain_of_thought",
  "style_variation",
];
const DEFAULT_COMPARE_SET: PromptTechnique[] = [
  "role",
  "few_shot",
  "chain_of_thought",
  "style_variation",
];

function titleCase(value: string): string {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function App() {
  const [question, setQuestion] = useState(
    "Design a production-ready rollout strategy for introducing AI summaries in a SaaS product.",
  );
  const [persona, setPersona] = useState<Persona>("architect");
  const [style, setStyle] = useState<PromptStyle>("technical");
  const [technique, setTechnique] = useState<PromptTechnique>("auto");
  const [compareTechniques, setCompareTechniques] = useState<PromptTechnique[]>(
    DEFAULT_COMPARE_SET,
  );

  const [singleResponse, setSingleResponse] = useState<AskResponse | null>(null);
  const [compareResponses, setCompareResponses] = useState<AskResponse[]>([]);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [activeTrace, setActiveTrace] = useState<TraceStep[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetchGraph()
      .then((payload) => setGraph(payload))
      .catch(() => {
        setError("Could not load workflow graph. Ensure the backend is running.");
      });
  }, []);

  const visibleResponses = useMemo(() => {
    if (compareResponses.length > 0) {
      return compareResponses;
    }
    if (singleResponse) {
      return [singleResponse];
    }
    return [];
  }, [compareResponses, singleResponse]);

  async function handleAsk(): Promise<void> {
    setLoading(true);
    setError("");
    setCompareResponses([]);

    try {
      const response = await askQuestion({
        question,
        persona,
        style,
        technique,
      });

      setSingleResponse(response);
      setActiveTrace(response.trace);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Request failed.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCompare(): Promise<void> {
    setLoading(true);
    setError("");
    setSingleResponse(null);

    try {
      const response = await comparePromptTechniques({
        question,
        persona,
        style,
        techniques: compareTechniques,
      });

      setCompareResponses(response.responses);
      setActiveTrace(response.responses[0]?.trace ?? []);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Request failed.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  function toggleTechnique(item: PromptTechnique): void {
    setCompareTechniques((current) => {
      if (current.includes(item)) {
        if (current.length === 2) {
          return current;
        }
        return current.filter((value) => value !== item);
      }
      return [...current, item];
    });
  }

  return (
    <div className="page-shell">
      <header className="hero-panel">
        <p className="hero-kicker">Prompt Engineering Studio</p>
        <h1>Smart Q&A Assistant</h1>
        <p>
          Compare role prompting, few-shot prompting, chain-of-thought, and style-driven prompts
          with a live LangGraph execution pipeline.
        </p>
      </header>

      <section className="layout-grid">
        <aside className="control-panel">
          <h2>Conversation Controls</h2>

          <label htmlFor="question">Question</label>
          <textarea
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={7}
          />

          <div className="row-fields">
            <div>
              <label htmlFor="persona">Persona</label>
              <select
                id="persona"
                value={persona}
                onChange={(event) => setPersona(event.target.value as Persona)}
              >
                {PERSONAS.map((item) => (
                  <option key={item} value={item}>
                    {titleCase(item)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="style">Prompt Style</label>
              <select
                id="style"
                value={style}
                onChange={(event) => setStyle(event.target.value as PromptStyle)}
              >
                {PROMPT_STYLES.map((item) => (
                  <option key={item} value={item}>
                    {titleCase(item)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <label htmlFor="technique">Single Technique</label>
          <select
            id="technique"
            value={technique}
            onChange={(event) => setTechnique(event.target.value as PromptTechnique)}
          >
            {TECHNIQUES.map((item) => (
              <option key={item} value={item}>
                {titleCase(item)}
              </option>
            ))}
          </select>

          <fieldset>
            <legend>Compare Techniques</legend>
            <p className="hint">Choose at least two techniques for side-by-side comparison.</p>
            {DEFAULT_COMPARE_SET.map((item) => (
              <label key={item} className="checkbox-row">
                <input
                  type="checkbox"
                  checked={compareTechniques.includes(item)}
                  onChange={() => toggleTechnique(item)}
                />
                <span>{titleCase(item)}</span>
              </label>
            ))}
          </fieldset>

          <div className="action-row">
            <button type="button" onClick={handleAsk} disabled={loading || question.trim().length < 3}>
              Run Single
            </button>
            <button
              type="button"
              className="secondary"
              onClick={handleCompare}
              disabled={loading || question.trim().length < 3 || compareTechniques.length < 2}
            >
              Compare
            </button>
          </div>

          {loading && <p className="status">Generating response...</p>}
          {error && <p className="error">{error}</p>}
        </aside>

        <section className="results-panel">
          <header>
            <h2>Responses</h2>
            <p>Tap a response card to sync execution trace with the LangGraph view.</p>
          </header>

          {visibleResponses.length === 0 && !loading && (
            <div className="empty-state">
              Choose a persona and prompt strategy, then run a query to inspect the result.
            </div>
          )}

          {compareResponses.length > 0 && (
            <div className="compare-grid">
              {compareResponses.map((item, index) => (
                <ResponseCard
                  key={`${item.technique}-${index}`}
                  response={item}
                  onSelectTrace={(selected) => setActiveTrace(selected.trace)}
                />
              ))}
            </div>
          )}

          {singleResponse && compareResponses.length === 0 && (
            <ResponseCard
              response={singleResponse}
              onSelectTrace={(selected) => setActiveTrace(selected.trace)}
            />
          )}
        </section>
      </section>

      <GraphFlow graph={graph} trace={activeTrace} />
    </div>
  );
}

export default App;
