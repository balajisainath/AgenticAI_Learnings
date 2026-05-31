import { useCallback, useEffect, useRef, useState } from 'react';
import './App.css';
import { sendMessage, fetchHealth } from './api';
import type { Conversation, Message, Provider } from './types';
import { Sidebar } from './components/Sidebar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { WelcomeScreen } from './components/WelcomeScreen';

// ── ID helpers ────────────────────────────────────────────────────────────────
function uid() { return Math.random().toString(36).slice(2, 10); }

function makeConversation(provider: Provider): Conversation {
  return { id: uid(), title: 'New chat', messages: [], createdAt: new Date(), provider };
}

// ── Typing indicator ──────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '4px 0' }}>
      <div style={{
        width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#2a2a2a', border: '1px solid var(--border)',
        fontSize: '0.8rem', color: 'var(--text-secondary)',
      }}>
        🛡
      </div>
      <div style={{
        background: 'var(--bg-bubble-bot)', border: '1px solid var(--border)',
        borderRadius: '18px 18px 18px 4px', padding: '12px 16px',
        display: 'flex', gap: 5, alignItems: 'center',
      }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 7, height: 7, borderRadius: '50%', background: 'var(--text-muted)',
            animation: `bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
          }} />
        ))}
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [provider, setProvider] = useState<Provider>('openai');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string>('');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [guardrailsStatus, setGuardrailsStatus] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [guardrailsAiEnabled, setGuardrailsAiEnabled] = useState(true);
  const [nemoEnabled, setNemoEnabled] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Get active conversation
  const activeConv = conversations.find(c => c.id === activeId) ?? null;

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConv?.messages.length, loading]);

  // Fetch guardrails status on mount
  useEffect(() => {
    fetchHealth().then(data => {
      if (data.guardrails) setGuardrailsStatus(data.guardrails as Record<string, unknown>);
    }).catch(() => {/* backend not up yet */});
  }, []);

  // ── Conversation management ───────────────────────────────────────────────

  const newConversation = useCallback(() => {
    const conv = makeConversation(provider);
    setConversations(prev => [conv, ...prev]);
    setActiveId(conv.id);
    setInput('');
    setError('');
  }, [provider]);

  // Create first conversation on mount
  useEffect(() => {
    if (conversations.length === 0) newConversation();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function deleteConversation(id: string) {
    setConversations(prev => {
      const next = prev.filter(c => c.id !== id);
      if (id === activeId) {
        if (next.length > 0) setActiveId(next[0].id);
        else {
          const fresh = makeConversation(provider);
          setActiveId(fresh.id);
          return [fresh, ...next];
        }
      }
      return next;
    });
  }

  function updateConversation(id: string, updater: (c: Conversation) => Conversation) {
    setConversations(prev => prev.map(c => c.id === id ? updater(c) : c));
  }

  // ── Sending a message ─────────────────────────────────────────────────────

  async function handleSend() {
    if (!input.trim() || loading) return;
    setError('');

    // Ensure we have an active conversation
    let convId = activeId;
    if (!convId) {
      const conv = makeConversation(provider);
      setConversations(prev => [conv, ...prev]);
      setActiveId(conv.id);
      convId = conv.id;
    }

    const userMsg: Message = {
      id: uid(), role: 'user', content: input.trim(), timestamp: new Date(),
    };

    // Derive history before adding current message
    const currentConv = conversations.find(c => c.id === convId);
    const history = (currentConv?.messages ?? []).map(m => ({ role: m.role, content: m.content }));

    // Optimistically add user message + update title if first message
    updateConversation(convId, conv => ({
      ...conv,
      title: conv.messages.length === 0 ? input.trim().slice(0, 40) : conv.title,
      messages: [...conv.messages, userMsg],
    }));
    setInput('');
    setLoading(true);

    try {
      abortRef.current = new AbortController();
      const res = await sendMessage({
        message: userMsg.content,
        session_id: convId,
        history,
        provider,
        guardrails_ai_enabled: guardrailsAiEnabled,
        nemo_enabled: nemoEnabled,
      });

      const botMsg: Message = {
        id: uid(),
        role: 'assistant',
        content: res.message,
        guardrails: res.guardrails,
        trace: res.trace,
        metadata: res.metadata,
        timestamp: new Date(),
      };

      updateConversation(convId, conv => ({
        ...conv,
        messages: [...conv.messages, botMsg],
      }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Request failed.';
      if (msg !== 'AbortError') setError(msg);
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  function handleStop() {
    abortRef.current?.abort();
    setLoading(false);
  }

  function handleExample(text: string) {
    setInput(text);
  }

  const messages = activeConv?.messages ?? [];
  const showWelcome = messages.length === 0 && !loading;

  return (
    <>
      {/* Bounce animation for typing dots */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .conv-delete-btn { opacity: 0 !important; }
        div:hover > div > .conv-delete-btn { opacity: 1 !important; }
      `}</style>

      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        {/* ── Sidebar ───────────────────────────────────────────────────── */}
        <Sidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={newConversation}
          onDelete={deleteConversation}
          provider={provider}
          onProviderChange={p => { setProvider(p); }}
          guardrailsStatus={guardrailsStatus}
          guardrailsAiEnabled={guardrailsAiEnabled}
          nemoEnabled={nemoEnabled}
          onToggleGuardrailsAi={setGuardrailsAiEnabled}
          onToggleNemo={setNemoEnabled}
        />

        {/* ── Main chat area ────────────────────────────────────────────── */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg-chat)' }}>
          {/* Top bar */}
          <div style={{
            padding: '14px 24px',
            borderBottom: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', gap: 10,
            background: 'var(--bg-chat)',
          }}>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
              {activeConv?.title ?? 'SafeBot'}
            </span>
            {activeConv && messages.length > 0 && (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                {messages.length} message{messages.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
            <div style={{ maxWidth: 780, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {showWelcome ? (
                <WelcomeScreen onExample={handleExample} />
              ) : (
                messages.map(msg => <ChatMessage key={msg.id} message={msg} />)
              )}

              {loading && <TypingDots />}

              {error && (
                <div style={{
                  background: '#1a0808', border: '1px solid #7f1d1d',
                  borderRadius: 'var(--radius-sm)', padding: '10px 14px',
                  color: '#fca5a5', fontSize: '0.84rem',
                }}>
                  {error}
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          </div>

          {/* Input */}
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            onStop={handleStop}
            loading={loading}
            placeholder={showWelcome ? 'Ask SafeBot anything…' : 'Continue the conversation…'}
          />
        </main>
      </div>
    </>
  );
}
