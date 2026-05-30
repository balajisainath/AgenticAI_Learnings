import type { GraphResponse, TraceStep } from "../types";

interface GraphFlowProps {
  graph: GraphResponse | null;
  trace: TraceStep[];
}

function hasNode(trace: TraceStep[], nodeId: string): boolean {
  return trace.some((step) => step.node === nodeId);
}

export function GraphFlow({ graph, trace }: GraphFlowProps) {
  if (!graph) {
    return <div className="graph-panel">Loading graph...</div>;
  }

  const nodeWidth = 156;
  const nodeHeight = 46;
  const maxX = Math.max(...graph.nodes.map((node) => node.x + nodeWidth), 1200) + 40;
  const maxY = Math.max(...graph.nodes.map((node) => node.y + nodeHeight), 180) + 30;

  return (
    <section className="graph-panel">
      <header className="graph-header">
        <h3>{graph.title}</h3>
        <p>Execution trace highlights nodes selected in the latest run.</p>
      </header>

      <div className="graph-canvas" role="img" aria-label="LangGraph execution view">
        <svg viewBox={`0 0 ${maxX} ${maxY}`} preserveAspectRatio="xMidYMid meet">
          {graph.edges.map((edge) => {
            const source = graph.nodes.find((node) => node.id === edge.source);
            const target = graph.nodes.find((node) => node.id === edge.target);
            if (!source || !target) {
              return null;
            }

            const edgeActive = hasNode(trace, source.id) && hasNode(trace, target.id);
            return (
              <line
                key={`${edge.source}-${edge.target}`}
                x1={source.x + nodeWidth}
                y1={source.y + nodeHeight / 2}
                x2={target.x}
                y2={target.y + nodeHeight / 2}
                className={edgeActive ? "graph-edge active" : "graph-edge"}
              />
            );
          })}

          {graph.nodes.map((node) => {
            const active = hasNode(trace, node.id);
            return (
              <g key={node.id}>
                <rect
                  x={node.x}
                  y={node.y}
                  width={nodeWidth}
                  height={nodeHeight}
                  rx={10}
                  className={active ? "graph-node active" : "graph-node"}
                />
                <text
                  x={node.x + nodeWidth / 2}
                  y={node.y + nodeHeight / 2 + 4}
                  textAnchor="middle"
                  className="graph-node-label"
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <ol className="trace-list">
        {trace.length === 0 && <li>No execution yet.</li>}
        {trace.map((step, index) => (
          <li key={`${step.node}-${index}`}>
            <strong>{step.node}</strong>
            <span>{step.detail}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
