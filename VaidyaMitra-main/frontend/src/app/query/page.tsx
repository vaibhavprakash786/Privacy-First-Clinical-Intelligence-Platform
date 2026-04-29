'use client';
import { useState, useRef, useEffect, type CSSProperties } from 'react';
import { aiQuery } from '@/lib/api';
import { styles } from '@/lib/styles';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    agent?: string;
    confidence?: number;
    timestamp: Date;
}

const EXAMPLES = [
    { icon: '📋', text: 'Summarize the patient\'s clinical history' },
    { icon: '💊', text: 'What are the generic alternatives for Augmentin?' },
    { icon: '🤒', text: 'I have fever, cough, and body pain — what could it be?' },
    { icon: '🧪', text: 'What tests should I recommend for diabetes monitoring?' },
    { icon: '💉', text: 'Explain the side effects of Metformin' },
    { icon: '📊', text: 'Compare blood pressure trends for the patient' },
];

/* ======= Styles ======= */
const fieldInput: CSSProperties = {
    width: '100%', boxSizing: 'border-box', padding: '12px 16px', borderRadius: '12px',
    color: 'var(--text-input)', background: 'var(--bg-input)', border: '1px solid var(--border-input)',
    outline: 'none', fontSize: '14px', transition: 'border-color 0.2s, background 0.3s, color 0.3s',
};

const msgBubbleUser: CSSProperties = {
    maxWidth: '80%', padding: '10px 16px', borderRadius: '16px 16px 4px 16px',
    background: 'var(--msg-user-bg)', color: 'var(--text-primary)', fontSize: '14px', lineHeight: 1.6,
    border: 'var(--msg-user-border)',
};

const msgBubbleAssistant: CSSProperties = {
    maxWidth: '80%', padding: '12px 16px', borderRadius: '16px 16px 16px 4px',
    background: 'var(--msg-assistant-bg)', color: 'var(--msg-assistant-text)', fontSize: '14px', lineHeight: 1.6,
    border: 'var(--msg-assistant-border)',
};

/* ======= Main Component ======= */
export default function QueryPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [patientId, setPatientId] = useState('');
    const [loading, setLoading] = useState(false);
    const endRef = useRef<HTMLDivElement>(null);
    useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

    const handleSend = async (query?: string) => {
        const q = query || input;
        if (!q.trim()) return;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: q, timestamp: new Date() }]);
        setLoading(true);
        try {
            const res = await aiQuery(q, patientId || undefined);
            const d = res.data as Record<string, unknown>;
            const r = d?.result as Record<string, unknown>;
            let content = '';

            if (d?.agent === 'error') {
                content = String(d?.error || 'Agent encountered an unknown error during orchestration.');
            } else {
                content = String(r?.response || r?.summary_text || r?.ai_explanation || JSON.stringify(r, null, 2));
            }
            setMessages(prev => [...prev, {
                role: 'assistant', content, agent: String(d?.agent || 'ai'),
                confidence: Number(d?.intent_confidence || 0), timestamp: new Date(),
            }]);
        } catch (err: unknown) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Error: ${err instanceof Error ? err.message : 'Query failed'}. Make sure the backend is running.`,
                timestamp: new Date(),
            }]);
        } finally { setLoading(false); }
    };

    const handlePatientIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value.toUpperCase().replace(/[^A-Z0-9\-]/g, '').slice(0, 12);
        setPatientId(val);
    };

    return (
        <main style={styles.mainContent}>
            <div style={{ display: 'flex', flexDirection: 'column' as const, height: 'calc(100vh - 5rem)' }}>
                {/* Header */}
                <div style={{ marginBottom: '12px' }}>
                    <h1 style={styles.pageTitle}>🤖 AI Query Assistant</h1>
                    <p style={styles.pageSubtitle}>Agentic AI routes your query to the right sub-agent · Privacy masking applied automatically</p>
                </div>

                {/* Context Bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                    <label style={{ fontSize: '11px', color: 'var(--label-text)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', fontWeight: 600, whiteSpace: 'nowrap' as const }}>Patient Context:</label>
                    <input
                        id="patient-context"
                        placeholder="Optional Patient ID (e.g., VM-ABC123)"
                        value={patientId}
                        onChange={handlePatientIdChange}
                        maxLength={12}
                        style={{ ...fieldInput, maxWidth: '240px', padding: '8px 12px', fontSize: '13px' }}
                    />
                    {patientId && (
                        <span style={{
                            padding: '4px 10px', borderRadius: '8px', fontSize: '11px',
                            background: 'rgba(34,211,238,0.08)', color: 'rgba(34,211,238,0.7)',
                            border: '1px solid rgba(34,211,238,0.15)',
                        }}>🔗 Linked to: {patientId}</span>
                    )}
                </div>

                {/* Chat Area */}
                <div style={{
                    ...styles.glassCard, flex: 1, overflowY: 'auto' as const,
                    display: 'flex', flexDirection: 'column' as const, gap: '12px',
                    padding: '16px', marginBottom: '12px',
                }}>
                    {messages.length === 0 && (
                        <div style={{ textAlign: 'center' as const, paddingTop: '40px' }}>
                            <div style={{ fontSize: '48px', marginBottom: '12px' }}>🤖</div>
                            <p style={{ color: 'var(--text-muted)', fontSize: '15px', marginBottom: '24px' }}>
                                Ask about clinical data, disease prediction, or medicine alternatives
                            </p>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', maxWidth: '500px', margin: '0 auto' }}>
                                {EXAMPLES.map((q, i) => (
                                    <button key={i} onClick={() => handleSend(q.text)} style={{
                                        textAlign: 'left' as const, padding: '10px 14px', borderRadius: '10px',
                                        fontSize: '13px', color: 'var(--chip-inactive-text)', cursor: 'pointer',
                                        background: 'var(--chip-inactive-bg)', border: 'var(--msg-assistant-border)',
                                        transition: 'all 0.2s',
                                    }}>
                                        <span style={{ marginRight: '6px' }}>{q.icon}</span>
                                        {q.text}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                            <div style={msg.role === 'user' ? msgBubbleUser : msgBubbleAssistant}>
                                {msg.agent && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                                        <span style={{
                                            fontSize: '10px', textTransform: 'uppercase' as const,
                                            letterSpacing: '0.06em', fontWeight: 600, color: 'var(--accent-primary)',
                                        }}>{msg.agent.replace('_', ' ')} agent</span>
                                        {msg.confidence !== undefined && msg.confidence > 0 && (
                                            <span style={{ fontSize: '10px', color: 'var(--label-text)' }}>
                                                ({(msg.confidence * 100).toFixed(0)}% conf)
                                            </span>
                                        )}
                                    </div>
                                )}
                                <p style={{ margin: 0, whiteSpace: 'pre-wrap' as const }}>{msg.content}</p>
                                <p style={{ fontSize: '10px', color: 'var(--text-dimmed)', margin: '6px 0 0' }}>
                                    {msg.timestamp.toLocaleTimeString()}
                                </p>
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                            <div style={{ ...msgBubbleAssistant, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '12px' }}>⏳</span>
                                <span style={{ fontSize: '13px', color: 'rgba(148,163,184,0.5)' }}>Processing through agents...</span>
                            </div>
                        </div>
                    )}
                    <div ref={endRef} />
                </div>

                {/* Input Bar */}
                <div style={{ display: 'flex', gap: '10px' }}>
                    <input
                        id="query-input"
                        placeholder="Ask about clinical data, diseases, medicines..."
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                        disabled={loading}
                        style={{ ...fieldInput, padding: '14px 16px', fontSize: '15px' }}
                    />
                    <button
                        id="btn-send-query"
                        onClick={() => handleSend()}
                        disabled={loading || !input.trim()}
                        style={{
                            ...styles.btnPrimary, padding: '14px 28px', fontSize: '15px',
                            opacity: loading || !input.trim() ? 0.5 : 1,
                        }}
                    >
                        {loading ? '⏳' : '➜ Send'}
                    </button>
                </div>
            </div>
        </main>
    );
}
