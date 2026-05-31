import type { GraphResponse, StreamEvent } from "../types";

interface GraphFlowProps {
  graph: GraphResponse | null;
  activeNodes: string[];
  streamLog: StreamEvent[];
}

export function GraphFlow({ graph, activeNodes, streamLog }: GraphFlowProps) {
  if (!graph) {
    return <div className="graph-panel">Loading graph...</div>;
  }

  return (
    <section className="graph-panel">
      <div className="graph-header">
        <h3>Execution Pipeline</h3>
        {activeNodes.length > 0 && (
          <span className="graph-status">
            {activeNodes.length === graph.nodes.length ? "Complete" : "Executing..."}
          </span>
        )}
      </div>

      <div className="graph-canvas">
        <svg width="1240" height="120" viewBox="0 0 1240 120">
          {graph.edges.map((edge) => {
            const source = graph.nodes.find((n) => n.id === edge.source);
            const target = graph.nodes.find((n) => n.id === edge.target);
            if (!source || !target) return null;

            const active = activeNodes.includes(source.id) && activeNodes.includes(target.id);
            return (
              <line
                key={`${edge.source}-${edge.target}`}
                x1={source.x + 64}
                y1={60}
                x2={target.x}
                y2={60}
                className={`graph-edge ${active ? "active" : ""}`}
              />
            );
          })}

          {graph.nodes.map((node) => {
            const active = activeNodes.includes(node.id);
            return (
              <g key={node.id}>
                <rect
                  x={node.x}
                  y={38}
                  width={128}
                  height={44}
                  rx={8}
                  className={`graph-node ${active ? "active" : ""}`}
                />
                <text x={node.x + 64} y={65} textAnchor="middle" className="graph-node-label">
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {streamLog.length > 0 && (
        <div className="stream-log">
          {streamLog.map((event, i) => (
            <div key={i} className={`log-entry ${event.type}`}>
              <span className="log-node">{event.node}</span>
              <span className="log-detail">{event.detail}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
