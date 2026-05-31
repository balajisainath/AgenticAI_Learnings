import Markdown from "react-markdown";
import type { AskResponse } from "../types";

interface ResponseCardProps {
  response: AskResponse;
}

function prettifyTechnique(value: string): string {
  return value
    .split("_")
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(" ");
}

export function ResponseCard({ response }: ResponseCardProps) {
  return (
    <article className="response-card">
      <header className="response-card-header">
        <span className="response-technique">{prettifyTechnique(response.technique)}</span>
        <span className="response-model">{response.metadata.model}</span>
      </header>
      <div className="response-answer markdown-body">
        <Markdown>{response.answer}</Markdown>
      </div>
      <details className="prompt-preview">
        <summary>View Prompt</summary>
        <pre>{response.prompt_preview}</pre>
      </details>
    </article>
  );
}
