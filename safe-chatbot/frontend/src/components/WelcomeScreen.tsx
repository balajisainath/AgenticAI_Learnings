import { Shield, Zap, Lock, Eye } from 'lucide-react';

const EXAMPLES = [
  { icon: <Zap size={20} />, text: 'Explain quantum computing in simple terms' },
  { icon: <Lock size={20} />, text: 'What are the best practices for API security?' },
  { icon: <Eye size={20} />, text: 'How does machine learning work?' },
  { icon: <Shield size={20} />, text: 'Summarize the history of the internet' },
];

interface WelcomeScreenProps {
  onExample: (text: string) => void;
}

export function WelcomeScreen({ onExample }: WelcomeScreenProps) {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '40px 20px', gap: 32,
    }}>
      {/* Logo + title */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: 64, height: 64, borderRadius: '50%',
          background: 'linear-gradient(135deg, #1d4ed8, #7c3aed)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 20px', boxShadow: '0 0 40px rgba(37,99,235,0.3)',
        }}>
          <Shield size={30} color="#fff" />
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 10 }}>
          SafeBot
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', maxWidth: 460, lineHeight: 1.6 }}>
          An AI assistant with dual-layer safety — every message passes through{' '}
          <span style={{ color: 'var(--badge-grails)', fontWeight: 600 }}>Guardrails AI</span> validators and{' '}
          <span style={{ color: 'var(--badge-nemo)', fontWeight: 600 }}>NVIDIA NeMo Guardrails</span> before reaching the LLM.
        </p>
      </div>

      {/* Layer cards */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 680 }}>
        <LayerCard
          title="Guardrails AI"
          subtitle="Layer 1 — Input & Output"
          color="var(--badge-grails)"
          items={['Harmful content detection', 'Jailbreak pattern matching', 'Profanity filtering', 'PII redaction in output']}
        />
        <LayerCard
          title="NeMo Guardrails"
          subtitle="Layer 2 — Dialog Rails"
          color="var(--badge-nemo)"
          items={['Colang intent classification', 'Hate speech flows', 'Dangerous activity flows', 'Greeting & persona flows']}
        />
      </div>

      {/* Example prompts */}
      <div style={{ width: '100%', maxWidth: 580 }}>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', textAlign: 'center', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
          Try an example
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              onClick={() => onExample(ex.text)}
              style={{
                background: 'var(--bg-input)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius)', color: 'var(--text-secondary)',
                padding: '12px 14px', cursor: 'pointer', textAlign: 'left',
                fontSize: '0.84rem', display: 'flex', alignItems: 'center',
                gap: 10, transition: 'var(--transition)', lineHeight: 1.4,
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = '#222';
                e.currentTarget.style.borderColor = 'var(--border-light)';
                e.currentTarget.style.color = 'var(--text-primary)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'var(--bg-input)';
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              <span style={{ color: 'var(--accent)', flexShrink: 0 }}>{ex.icon}</span>
              {ex.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function LayerCard({ title, subtitle, color, items }: {
  title: string; subtitle: string; color: string; items: string[];
}) {
  return (
    <div style={{
      background: 'var(--bg-input)', border: `1px solid ${color}44`,
      borderRadius: 'var(--radius)', padding: '16px 18px', flex: '1 1 240px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, boxShadow: `0 0 8px ${color}` }} />
        <div>
          <p style={{ fontSize: '0.85rem', fontWeight: 700, color }}>{title}</p>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{subtitle}</p>
        </div>
      </div>
      <ul style={{ paddingLeft: 16, color: 'var(--text-secondary)', fontSize: '0.8rem', lineHeight: 1.8 }}>
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    </div>
  );
}
