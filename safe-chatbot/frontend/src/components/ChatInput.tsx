import { useRef, useEffect, type KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onStop?: () => void;
  loading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ value, onChange, onSend, onStop, loading, disabled, placeholder }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }, [value]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading && value.trim()) onSend();
    }
  }

  const canSend = !loading && !disabled && value.trim().length > 0;

  return (
    <div style={{
      padding: '12px 16px 20px',
      background: 'var(--bg-chat)',
      borderTop: '1px solid var(--border)',
    }}>
      <div style={{
        maxWidth: 780,
        margin: '0 auto',
        background: 'var(--bg-input)',
        border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        display: 'flex',
        alignItems: 'flex-end',
        gap: 8,
        padding: '8px 8px 8px 14px',
        boxShadow: '0 0 0 1px transparent',
        transition: 'box-shadow var(--transition)',
      }}
        onFocus={e => (e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent-glow)')}
        onBlur={e => (e.currentTarget.style.boxShadow = '0 0 0 1px transparent')}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? 'Message SafeBot… (Shift+Enter for new line)'}
          disabled={loading || disabled}
          rows={1}
          style={{
            flex: 1, resize: 'none', border: 'none', outline: 'none',
            background: 'transparent', color: 'var(--text-primary)',
            fontSize: '0.92rem', lineHeight: 1.6, fontFamily: 'var(--font-sans)',
            maxHeight: 200, overflowY: 'auto', paddingTop: 4, paddingBottom: 4,
          }}
        />

        {loading ? (
          <button
            onClick={onStop}
            title="Stop"
            style={{
              background: '#333', border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-sm)', cursor: 'pointer',
              color: 'var(--text-secondary)', padding: '7px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, transition: 'var(--transition)',
            }}
          >
            <Square size={16} />
          </button>
        ) : (
          <button
            onClick={onSend}
            disabled={!canSend}
            title="Send (Enter)"
            style={{
              background: canSend ? 'var(--accent)' : '#222',
              border: '1px solid ' + (canSend ? 'transparent' : 'var(--border)'),
              borderRadius: 'var(--radius-sm)', cursor: canSend ? 'pointer' : 'not-allowed',
              color: canSend ? '#fff' : 'var(--text-muted)',
              padding: '7px', display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, transition: 'var(--transition)',
            }}
          >
            <Send size={16} />
          </button>
        )}
      </div>

      <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.7rem', marginTop: 8 }}>
        Protected by <strong style={{ color: 'var(--badge-grails)' }}>Guardrails AI</strong> + <strong style={{ color: 'var(--badge-nemo)' }}>NVIDIA NeMo Guardrails</strong>
      </p>
    </div>
  );
}
