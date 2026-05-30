import type { TraceStep } from "../types";

interface ResponseCardData {
  title: string;
  body: string;
  tag: string;
  trace: TraceStep[];
}

interface ResponseCardProps {
  response: ResponseCardData;
  onSelectTrace?: (response: ResponseCardData) => void;
}

function prettifyTag(value: string): string {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function ResponseCard({ response, onSelectTrace }: ResponseCardProps) {
  return (
    <article className="response-card" onClick={() => onSelectTrace?.(response)}>
      <header className="response-card-header">
        <span className="response-technique">{prettifyTag(response.tag)}</span>
        <span className="response-model">Trace: {response.trace.length}</span>
      </header>
      <p className="response-answer">{response.body}</p>
      <details className="prompt-preview">
        <summary>Card Details</summary>
        <pre>{response.title}</pre>
      </details>
    </article>
  );
}
