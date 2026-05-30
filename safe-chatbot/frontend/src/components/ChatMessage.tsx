import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Shield, AlertTriangle, CheckCircle, ChevronDown, ChevronRight, Filter } from 'lucide-react';
import { useState } from 'react';
import type { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isBlocked = message.guardrails?.input_blocked;
  const isFiltered = message.guardrails?.output_filtered;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      gap: 6,
      padding: '4px 0',
      animation: 'fadeSlideIn 200ms ease',
    }}>
      {/* ── Avatar + bubble row ─────────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10,
        flexDirection: isUser ? 'row-reverse' : 'row',
        maxWidth: '78%',
      }}>
        {/* Avatar */}
        <div style={{
          width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.8rem', fontWeight: 700, userSelect: 'none',
          background: isUser ? 'var(--accent)' : '#2a2a2a',
          color: isUser ? '#fff' : 'var(--text-secondary)',
          border: isUser ? 'none' : '1px solid var(--border)',
        }}>
          {isUser ? 'U' : <Shield size={15} />}
        </div>

        {/* Bubble */}
        <div style={{
          background: isUser
            ? 'var(--bg-bubble-user)'
            : isBlocked ? 'var(--bg-blocked)' : 'var(--bg-bubble-bot)',
          color: 'var(--text-primary)',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          padding: '10px 14px',
          fontSize: '0.9rem',
          lineHeight: 1.65,
          border: isBlocked ? '1px solid #7f1d1d'
            : isFiltered ? '1px solid #78350f'
            : isUser ? 'none'
            : '1px solid var(--border)',
          boxShadow: 'var(--shadow-sm)',
          wordBreak: 'break-word',
        }}>
          {isUser ? (
            <span>{message.content}</span>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      </div>

      {/* ── Guardrails metadata (bot messages only) ────────────────────── */}
      {!isUser && message.guardrails && (
        <GuardrailsBadges message={message} />
      )}
    </div>
  );
}

function GuardrailsBadges({ message }: { message: Message }) {
  const [showTrace, setShowTrace] = useState(false);
  const g = message.guardrails!;
  const grailsAI = g.guardrails_ai;
  const nemo = g.nemo;

  return (
    <div style={{ paddingLeft: 42, display: 'flex', flexDirection: 'column', gap: 4 }}>
      {/* ── Badge row ─────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, alignItems: 'center' }}>
        {/* Overall status */}
        {g.input_blocked ? (
          <Badge icon={<AlertTriangle size={11} />} label="Blocked" color="var(--badge-blocked)" bg="#3b0a0a" />
        ) : g.output_filtered ? (
          <Badge icon={<Filter size={11} />} label="Output filtered" color="var(--badge-filtered)" bg="#2d1b00" />
        ) : (
          <Badge icon={<CheckCircle size={11} />} label="Safe" color="var(--badge-safe)" bg="#052e16" />
        )}

        {/* Guardrails AI */}
        {grailsAI?.active && (
          <Badge
            label={`Guardrails AI${grailsAI.input_blocked ? ' ✗ input' : grailsAI.output_filtered ? ' ✗ output' : ' ✓'}`}
            color="var(--badge-grails)"
            bg="#052e16"
          />
        )}

        {/* NeMo */}
        {nemo?.active && (
          <Badge
            label={`NeMo${nemo.input_blocked ? ' ✗ blocked' : nemo.input_checked ? ' ✓' : ' —'}`}
            color="var(--badge-nemo)"
            bg="#1e0a3c"
          />
        )}

        {/* Model */}
        {message.metadata?.model && (
          <Badge
            label={message.metadata.model}
            color="var(--text-muted)"
            bg="#1a1a1a"
          />
        )}

        {/* Trace toggle */}
        {message.trace && message.trace.length > 0 && (
          <button
            onClick={() => setShowTrace(v => !v)}
            style={{
              background: 'none', border: '1px solid var(--border)', borderRadius: 99,
              color: 'var(--text-muted)', cursor: 'pointer',
              padding: '2px 8px', fontSize: '0.7rem',
              display: 'flex', alignItems: 'center', gap: 3,
            }}
          >
            {showTrace ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
            Trace
          </button>
        )}
      </div>

      {/* ── Trace panel ───────────────────────────────────────────────── */}
      {showTrace && message.trace && (
        <TracePanel steps={message.trace} />
      )}
    </div>
  );
}

function Badge({ icon, label, color, bg }: { icon?: React.ReactNode; label: string; color: string; bg: string }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: bg, color, border: `1px solid ${color}33`,
      borderRadius: 99, padding: '2px 8px', fontSize: '0.7rem', fontWeight: 600,
      letterSpacing: '0.02em',
    }}>
      {icon}{label}
    </span>
  );
}

function TracePanel({ steps }: { steps: { node: string; detail: string }[] }) {
  return (
    <div style={{
      background: '#111', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)', padding: '10px 12px',
      fontSize: '0.76rem', lineHeight: 1.6, marginTop: 2,
    }}>
      <p style={{ color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1, fontSize: '0.65rem' }}>
        LangGraph Trace
      </p>
      {steps.map((s, i) => (
        <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 6 }}>
          <span style={{
            background: '#1e1e1e', color: 'var(--accent)',
            border: '1px solid var(--border)', borderRadius: 4,
            padding: '1px 7px', fontSize: '0.68rem', flexShrink: 0,
            fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap',
          }}>
            {s.node}
          </span>
          <span style={{ color: 'var(--text-secondary)' }}>{s.detail}</span>
        </div>
      ))}
    </div>
  );
}
