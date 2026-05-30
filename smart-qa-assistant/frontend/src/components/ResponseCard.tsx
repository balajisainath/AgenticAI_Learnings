import type { AskResponse } from "../types";

interface ResponseCardProps {
  response: AskResponse;
  onSelectTrace?: (response: AskResponse) => void;
}

function prettifyTechnique(value: string): string {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function ResponseCard({ response, onSelectTrace }: ResponseCardProps) {
  return (
    <article className="response-card" onClick={() => onSelectTrace?.(response)}>
      <header className="response-card-header">
        <span className="response-technique">{prettifyTechnique(response.technique)}</span>
        <span className="response-model">{response.metadata.model}</span>
      </header>
      <p className="response-answer">{response.answer}</p>
      <details className="prompt-preview">
        <summary>Prompt Preview</summary>
        <pre>{response.prompt_preview}</pre>
      </details>
    </article>
  );
}
