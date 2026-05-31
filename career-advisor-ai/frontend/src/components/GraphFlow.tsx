import { useEffect, useMemo, useState } from "react";

import type { GraphResponse, TraceStep } from "../types";

interface GraphFlowProps {
  graph: GraphResponse | null;
  trace: TraceStep[];
  isRunning?: boolean;
  runningMode?: string;
}

function hasNode(trace: TraceStep[], nodeId: string): boolean {
  return trace.some((step) => step.node === nodeId);
}

export function GraphFlow({ graph, trace, isRunning = false, runningMode = "" }: GraphFlowProps) {
  const [playbackIndex, setPlaybackIndex] = useState(-1);
  const [runningIndex, setRunningIndex] = useState(-1);

  const orderedNodeIds = useMemo(() => {
    if (!graph) {
      return [];
    }
    return [...graph.nodes].sort((left, right) => left.x - right.x).map((node) => node.id);
  }, [graph]);

  useEffect(() => {
    if (trace.length === 0) {
      setPlaybackIndex(-1);
      return;
    }

    setPlaybackIndex(0);
    const timer = window.setInterval(() => {
      setPlaybackIndex((current) => {
        if (current >= trace.length - 1) {
          window.clearInterval(timer);
          return current;
        }
        return current + 1;
      });
    }, 420);

    return () => window.clearInterval(timer);
  }, [trace]);

  useEffect(() => {
    if (!isRunning || orderedNodeIds.length === 0) {
      setRunningIndex(-1);
      return;
    }

    setRunningIndex(0);
    const timer = window.setInterval(() => {
      setRunningIndex((current) => (current + 1) % orderedNodeIds.length);
    }, 520);

    return () => window.clearInterval(timer);
  }, [isRunning, orderedNodeIds]);

  if (!graph) {
    return <div className="graph-panel">Loading graph...</div>;
  }

  const nodeWidth = 156;
  const nodeHeight = 46;
  const maxX = Math.max(...graph.nodes.map((node) => node.x + nodeWidth), 1200) + 40;
  const maxY = Math.max(...graph.nodes.map((node) => node.y + nodeHeight), 180) + 30;

  const playedTrace = playbackIndex >= 0 ? trace.slice(0, playbackIndex + 1) : [];
  const completedNodes = new Set(playedTrace.map((step) => step.node));

  const runningNodes =
    isRunning && runningIndex >= 0 ? orderedNodeIds.slice(0, Math.min(runningIndex + 1, orderedNodeIds.length)) : [];
  const runningNodeSet = new Set(runningNodes);
  const currentRunningNode = isRunning && runningIndex >= 0 ? orderedNodeIds[runningIndex] : "";

  const liveTrace: TraceStep[] = runningNodes.map((nodeId, index) => ({
    node: nodeId,
    detail:
      index === runningNodes.length - 1
        ? `Running ${runningMode || "workflow"} step...`
        : "Completed in current run.",
  }));

  const renderedTrace = isRunning ? liveTrace : trace;

  return (
    <section className="graph-panel">
      <header className="graph-header">
        <h3>{graph.title}</h3>
        <p>
          {isRunning
            ? `Live flow is running (${runningMode || "workflow"}).`
            : playbackIndex >= 0 && playbackIndex < trace.length - 1
              ? "Replaying latest execution trace step-by-step."
              : "Execution trace and graph state update dynamically from backend responses."}
        </p>
      </header>

      <div className="graph-canvas" role="img" aria-label="LangGraph execution view">
        <svg viewBox={`0 0 ${maxX} ${maxY}`} preserveAspectRatio="xMidYMid meet">
          {graph.edges.map((edge) => {
            const source = graph.nodes.find((node) => node.id === edge.source);
            const target = graph.nodes.find((node) => node.id === edge.target);
            if (!source || !target) {
              return null;
            }

            const edgeCompleted =
              (hasNode(playedTrace, source.id) || completedNodes.has(source.id)) &&
              (hasNode(playedTrace, target.id) || completedNodes.has(target.id));
            const edgeRunning = runningNodeSet.has(source.id) && runningNodeSet.has(target.id);

            return (
              <line
                key={`${edge.source}-${edge.target}`}
                x1={source.x + nodeWidth}
                y1={source.y + nodeHeight / 2}
                x2={target.x}
                y2={target.y + nodeHeight / 2}
                className={edgeRunning ? "graph-edge running" : edgeCompleted ? "graph-edge active" : "graph-edge"}
              />
            );
          })}

          {graph.nodes.map((node) => {
            const active = completedNodes.has(node.id);
            const running = currentRunningNode === node.id;
            return (
              <g key={node.id}>
                <rect
                  x={node.x}
                  y={node.y}
                  width={nodeWidth}
                  height={nodeHeight}
                  rx={10}
                  className={running ? "graph-node running" : active ? "graph-node active" : "graph-node"}
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
        {renderedTrace.length === 0 && <li className="trace-item pending">No execution yet.</li>}
        {renderedTrace.map((step, index) => {
          const done = !isRunning && index <= playbackIndex;
          const current = isRunning ? index === renderedTrace.length - 1 : index === playbackIndex;
          const itemClass = current ? "trace-item current" : done || isRunning ? "trace-item done" : "trace-item pending";

          return (
            <li key={`${step.node}-${index}`} className={itemClass}>
              <strong>{step.node}</strong>
              <span>{step.detail}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
