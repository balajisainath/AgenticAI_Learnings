import { MessageSquare, Plus, Shield, Trash2 } from 'lucide-react';
import type { Conversation, Provider } from '../types';

interface SidebarProps {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  provider: Provider;
  onProviderChange: (p: Provider) => void;
  guardrailsStatus: Record<string, unknown> | null;
  guardrailsAiEnabled: boolean;
  nemoEnabled: boolean;
  onToggleGuardrailsAi: (v: boolean) => void;
  onToggleNemo: (v: boolean) => void;
}

const PROVIDERS: { value: Provider; label: string; color: string }[] = [
  { value: 'openai',       label: 'OpenAI GPT',       color: '#10a37f' },
  { value: 'anthropic',    label: 'Anthropic Claude',  color: '#d97706' },
  { value: 'google_genai', label: 'Google Gemini',     color: '#4285f4' },
];

export function Sidebar({
  conversations, activeId, onSelect, onNew, onDelete,
  provider, onProviderChange, guardrailsStatus,
  guardrailsAiEnabled, nemoEnabled, onToggleGuardrailsAi, onToggleNemo,
}: SidebarProps) {
  const gStatus = guardrailsStatus as Record<string, boolean> | null;

  return (
    <aside style={{
      width: 260,
      minWidth: 260,
      background: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div style={{ padding: '16px 14px 12px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Shield size={18} color="var(--accent)" />
          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            SafeBot
          </span>
          <span style={{
            marginLeft: 'auto', fontSize: '0.65rem', background: '#1e3a5f',
            color: '#60a5fa', padding: '2px 6px', borderRadius: 99, fontWeight: 600,
          }}>
            GUARDED
          </span>
        </div>

        {/* Provider picker */}
        <select
          value={provider}
          onChange={e => onProviderChange(e.target.value as Provider)}
          style={{
            width: '100%', background: '#222', color: 'var(--text-primary)',
            border: '1px solid var(--border-light)', borderRadius: 'var(--radius-sm)',
            padding: '7px 10px', fontSize: '0.82rem', cursor: 'pointer', outline: 'none',
          }}
        >
          {PROVIDERS.map(p => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
      </div>

      {/* ── New Chat button ───────────────────────────────────────────────── */}
      <div style={{ padding: '10px 10px 6px' }}>
        <button
          onClick={onNew}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', gap: 8,
            background: 'var(--accent)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-sm)',
            padding: '8px 12px', fontSize: '0.84rem', fontWeight: 600,
            cursor: 'pointer', transition: 'var(--transition)',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--accent-hover)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'var(--accent)')}
        >
          <Plus size={15} />
          New chat
        </button>
      </div>

      {/* ── Conversation list ─────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 8px' }}>
        {conversations.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', textAlign: 'center', marginTop: 24 }}>
            No conversations yet
          </p>
        )}
        {conversations.map(conv => (
          <ConvRow
            key={conv.id}
            conv={conv}
            isActive={conv.id === activeId}
            onSelect={onSelect}
            onDelete={onDelete}
          />
        ))}
      </div>

      {/* ── Guardrails toggle footer ──────────────────────────────────── */}
      <div style={{
        padding: '10px 14px 14px',
        borderTop: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', gap: 8,
      }}>
        <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 2 }}>
          Safety Layers
        </p>
        <ToggleRow
          label="Guardrails AI"
          color="var(--badge-grails)"
          enabled={guardrailsAiEnabled}
          onToggle={onToggleGuardrailsAi}
          available={!!gStatus?.guardrails_ai_active}
        />
        <ToggleRow
          label="NeMo Guardrails"
          color="var(--badge-nemo)"
          enabled={nemoEnabled}
          onToggle={onToggleNemo}
          available={!!gStatus?.nemo_active}
        />
      </div>
    </aside>
  );
}

function ConvRow({ conv, isActive, onSelect, onDelete }: {
  conv: Conversation;
  isActive: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const lastMsg = conv.messages[conv.messages.length - 1];
  const preview = lastMsg ? lastMsg.content.slice(0, 55) + (lastMsg.content.length > 55 ? '…' : '') : 'Empty chat';

  return (
    <div
      onClick={() => onSelect(conv.id)}
      style={{
        padding: '9px 10px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
        background: isActive ? 'var(--bg-sidebar-hover)' : 'transparent',
        border: isActive ? '1px solid var(--border-light)' : '1px solid transparent',
        marginBottom: 2, display: 'flex', alignItems: 'flex-start', gap: 8,
        transition: 'var(--transition)',
      }}
      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = '#1c1c1c'; }}
      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
    >
      <MessageSquare size={14} color="var(--text-muted)" style={{ marginTop: 2, flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: isActive ? 600 : 400, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {conv.title}
        </p>
        <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {preview}
        </p>
      </div>
      <button
        onClick={e => { e.stopPropagation(); onDelete(conv.id); }}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--text-muted)', padding: 2, borderRadius: 4,
          opacity: 0, transition: 'var(--transition)', flexShrink: 0,
        }}
        onMouseEnter={e => (e.currentTarget.style.color = '#ef4444')}
        onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
        className="conv-delete-btn"
        title="Delete"
      >
        <Trash2 size={13} />
      </button>
    </div>
  );
}

function ToggleRow({ label, color, enabled, onToggle, available }: {
  label: string;
  color: string;
  enabled: boolean;
  onToggle: (v: boolean) => void;
  available: boolean;
}) {
  const active = enabled && available;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
      <div style={{
        width: 7, height: 7, borderRadius: '50%',
        background: active ? color : '#444',
        boxShadow: active ? `0 0 6px ${color}` : 'none',
        flexShrink: 0,
      }} />
      <span style={{ fontSize: '0.75rem', color: active ? 'var(--text-secondary)' : 'var(--text-muted)', flex: 1 }}>
        {label}
      </span>
      {/* Toggle switch */}
      <button
        onClick={() => onToggle(!enabled)}
        title={!available ? 'Not available (backend not configured)' : enabled ? 'Disable' : 'Enable'}
        style={{
          position: 'relative',
          width: 34,
          height: 18,
          borderRadius: 9,
          border: 'none',
          cursor: available ? 'pointer' : 'not-allowed',
          background: active ? color : '#333',
          transition: 'background 0.2s',
          opacity: available ? 1 : 0.4,
          flexShrink: 0,
        }}
        disabled={!available}
      >
        <div style={{
          position: 'absolute',
          top: 2,
          left: active ? 18 : 2,
          width: 14,
          height: 14,
          borderRadius: '50%',
          background: '#fff',
          transition: 'left 0.2s',
          boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
        }} />
      </button>
    </div>
  );
}
