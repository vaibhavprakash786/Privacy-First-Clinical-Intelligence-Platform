'use client';
import { useState, type ReactNode } from 'react';
import { predictDisease } from '@/lib/api';

const COMMON_SYMPTOMS = [
    'Fever', 'Cough', 'Headache', 'Fatigue', 'Body Pain', 'Sore Throat',
    'Runny Nose', 'Nausea', 'Vomiting', 'Diarrhea', 'Chest Pain',
    'Shortness of Breath', 'Joint Pain', 'Skin Rash', 'Abdominal Pain',
    'Weight Loss', 'Frequent Urination', 'Dizziness', 'Blurred Vision', 'Back Pain',
    'Loss of Appetite', 'Excessive Thirst', 'Night Sweats', 'Swelling', 'Muscle Weakness',
];

const BODY_REGIONS = [
    { icon: '🧠', label: 'Head / Neuro', symptoms: ['Headache', 'Dizziness', 'Blurred Vision', 'Confusion'] },
    { icon: '💗', label: 'Chest / Cardiac', symptoms: ['Chest Pain', 'Shortness of Breath', 'Palpitations'] },
    { icon: '🫁', label: 'Respiratory', symptoms: ['Cough', 'Sore Throat', 'Runny Nose', 'Wheezing'] },
    { icon: '🤢', label: 'GI / Digestive', symptoms: ['Nausea', 'Vomiting', 'Diarrhea', 'Abdominal Pain'] },
    { icon: '💪', label: 'Musculoskeletal', symptoms: ['Joint Pain', 'Back Pain', 'Body Pain', 'Muscle Weakness'] },
    { icon: '🌡️', label: 'General', symptoms: ['Fever', 'Fatigue', 'Weight Loss', 'Night Sweats'] },
];

/* ======= Shared Classes ======= */
const inputClasses = "w-full box-border px-4 py-3 rounded-xl text-[14px] font-medium text-[var(--text-input)] bg-[var(--bg-input)] border border-[var(--border-input)] outline-none transition-all duration-200 focus:border-[var(--accent-primary)] focus:ring-4 focus:ring-[var(--accent-primary)]/10 placeholder:text-[var(--text-dimmed)] placeholder:font-normal hover:border-[var(--text-muted)] shadow-sm";
const cardClasses = "rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass)] shadow-[var(--shadow-card)] p-6 md:p-8 transition-all duration-300";

const activeChipClass = "bg-[var(--accent-primary)] text-white shadow-md shadow-sky-500/30 font-bold border-transparent hover:bg-sky-400 -translate-y-0.5";
const inactiveChipClass = "bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border-[var(--border-glass)] hover:border-sky-500/50 hover:bg-sky-500/5 hover:text-sky-600 dark:hover:text-sky-400 font-medium";

/* ======= Sub-components ======= */
function SectionHeader({ icon, title, subtitle }: { icon: string; title: string; subtitle?: string }) {
    return (
        <div className="mb-5">
            <div className="flex items-center gap-3">
                <span className="text-xl flex-shrink-0">{icon}</span>
                <h3 className="text-[16px] font-bold text-[var(--accent-primary)] m-0 tracking-tight">{title}</h3>
            </div>
            {subtitle && <p className="text-[13px] font-medium text-[var(--text-muted)] mt-1.5 ml-8 mb-0">{subtitle}</p>}
        </div>
    );
}

/* ======= Main Component ======= */
export default function PredictPage() {
    const [selected, setSelected] = useState<string[]>([]);
    const [custom, setCustom] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<Record<string, unknown> | null>(null);
    const [error, setError] = useState('');
    const [viewMode, setViewMode] = useState<'chips' | 'body'>('chips');

    const toggle = (s: string) => setSelected(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);
    const addCustom = () => {
        const val = custom.trim().replace(/[^a-zA-Z\s]/g, '');
        if (val && !selected.includes(val)) { setSelected(prev => [...prev, val]); setCustom(''); }
    };

    const handlePredict = async () => {
        if (selected.length === 0) { setError('Select at least one symptom'); return; }
        setLoading(true); setError(''); setResult(null);
        try {
            const res = await predictDisease(selected.map(s => s.toLowerCase()));
            setResult(res);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Prediction failed');
        } finally { setLoading(false); }
    };

    const data = result?.data as Record<string, unknown> | undefined;
    const predictions = (data?.predicted_diseases || []) as Array<{ disease: string; probability: number; confidence: number }>;
    const tests = (data?.recommended_tests || []) as string[];
    const explanation = String(data?.ai_explanation || '');
    const confidence = Number(data?.confidence_score || data?.confidence || 0);
    const reasoning = (data?.reasoning_steps || []) as Array<{ step_number: number; description: string; evidence: string; confidence: number }>;

    return (
        <main className="min-h-screen p-8 lg:p-12 transition-colors duration-200 bg-[var(--bg-main)]">
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--text-primary)] mb-2">🔬 Disease Prediction</h1>
            <p className="text-base text-[var(--text-secondary)] font-medium mb-8">AI-powered disease risk assessment · Select symptoms for analysis</p>

            <div className={`grid grid-cols-1 ${result ? 'xl:grid-cols-2' : ''} gap-8 transition-all duration-500`}>
                {/* ===== LEFT: Input ===== */}
                <div className="flex flex-col gap-5">
                    {/* View mode tabs */}
                    <div className="flex gap-3 bg-[var(--bg-glass)] p-1.5 rounded-xl border border-[var(--border-glass)] shadow-sm max-w-fit">
                        <button
                            onClick={() => setViewMode('chips')}
                            className={`px-5 py-2.5 rounded-lg text-[13px] font-bold transition-all duration-200 ${viewMode === 'chips' ? 'bg-[var(--accent-primary)] text-white shadow-sm' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]'}`}
                        >
                            🏷️ All Symptoms
                        </button>
                        <button
                            onClick={() => setViewMode('body')}
                            className={`px-5 py-2.5 rounded-lg text-[13px] font-bold transition-all duration-200 ${viewMode === 'body' ? 'bg-[var(--accent-primary)] text-white shadow-sm' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]'}`}
                        >
                            🫀 By Body Region
                        </button>
                    </div>

                    <div className={cardClasses}>
                        <SectionHeader icon="📋" title="Select Symptoms" subtitle={`${selected.length} selected · Click to toggle`} />

                        {viewMode === 'chips' ? (
                            <div className="flex flex-wrap gap-2.5 mb-6">
                                {COMMON_SYMPTOMS.map(s => {
                                    const isActive = selected.includes(s);
                                    return (
                                        <button
                                            key={s}
                                            onClick={() => toggle(s)}
                                            className={`px-4 py-2 rounded-full text-[13px] border transition-all duration-200 select-none ${isActive ? activeChipClass : inactiveChipClass}`}
                                        >
                                            {s}
                                        </button>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                                {BODY_REGIONS.map(region => (
                                    <div key={region.label} className="bg-[var(--bg-body)] rounded-xl p-4 border border-[var(--border-glass)] shadow-sm">
                                        <div className="text-[13px] text-sky-500 font-bold mb-3 tracking-tight">{region.icon} {region.label}</div>
                                        <div className="flex flex-wrap gap-2">
                                            {region.symptoms.map(s => {
                                                const isActive = selected.includes(s);
                                                return (
                                                    <button
                                                        key={s}
                                                        onClick={() => toggle(s)}
                                                        className={`px-3 py-1.5 rounded-lg text-[12px] border transition-all duration-200 select-none ${isActive ? activeChipClass : inactiveChipClass}`}
                                                    >
                                                        {s}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Custom symptom */}
                        <div className="flex flex-col sm:flex-row gap-3 mt-6 pt-6 border-t border-[var(--border-glass)]">
                            <input
                                id="custom-symptom"
                                placeholder="Add custom symptom..."
                                value={custom}
                                onChange={e => setCustom(e.target.value.replace(/[^a-zA-Z\s]/g, ''))}
                                onKeyDown={e => e.key === 'Enter' && addCustom()}
                                className={inputClasses}
                            />
                            <button
                                onClick={addCustom}
                                disabled={!custom.trim()}
                                className={`flex-shrink-0 px-6 py-3 bg-[var(--bg-chip)] text-[var(--text-primary)] border border-[var(--border-chip)] hover:border-[var(--accent-primary)] hover:bg-sky-500/10 font-bold rounded-xl shadow-sm transition-all duration-200 text-[14px] ${!custom.trim() ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                + Add
                            </button>
                        </div>

                        {/* Selected tags */}
                        {selected.length > 0 && (
                            <div className="mt-6 pt-5 border-t border-[var(--border-glass)] animate-in fade-in duration-300">
                                <div className="flex justify-between items-center mb-4">
                                    <span className="text-[11px] text-[var(--text-secondary)] uppercase tracking-widest font-bold">Selected ({selected.length})</span>
                                    <button
                                        onClick={() => setSelected([])}
                                        className="text-red-500 hover:text-red-600 dark:hover:text-red-400 font-bold text-[12px] transition-colors outline-none"
                                    >
                                        ✕ Clear All
                                    </button>
                                </div>
                                <div className="flex flex-wrap gap-2.5">
                                    {selected.map(s => (
                                        <span
                                            key={s}
                                            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-bold bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 shadow-sm"
                                        >
                                            {s}
                                            <button
                                                onClick={() => toggle(s)}
                                                className="w-5 h-5 flex items-center justify-center rounded-full hover:bg-sky-500/20 text-sky-500/70 hover:text-sky-600 transition-colors ml-1 outline-none font-normal"
                                            >
                                                ✕
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        <button
                            id="btn-predict"
                            onClick={handlePredict}
                            disabled={loading || selected.length === 0}
                            className={`w-full mt-8 px-6 py-4 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold rounded-xl shadow-[0_4px_14px_0_rgba(14,165,233,0.39)] hover:shadow-[0_6px_20px_0_rgba(14,165,233,0.39)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-md transition-all duration-200 text-[16px] flex justify-center items-center gap-2 ${loading || selected.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {loading ? '⏳ Analyzing Symptoms...' : `🔬 Predict Disease (${selected.length} symptoms)`}
                        </button>
                    </div>

                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 shadow-sm flex items-center gap-3">
                            <span className="text-xl">❌</span>
                            <p className="text-[14px] font-bold text-red-600 dark:text-red-400 m-0">{error}</p>
                        </div>
                    )}
                </div>

                {/* ===== RIGHT: Results ===== */}
                {result && (
                    <div className="flex flex-col gap-5 animate-in slide-in-from-right-8 fade-in duration-500">
                        {/* Predicted Conditions */}
                        <div className={cardClasses}>
                            <SectionHeader icon="🎯" title="Predicted Conditions" subtitle={`Overall confidence: ${(confidence * 100).toFixed(0)}%`} />
                            <div className="flex flex-col gap-4">
                                {predictions.map((p, i) => {
                                    const barColors = ['from-sky-400 to-sky-600', 'from-purple-400 to-purple-600', 'from-amber-400 to-amber-600', 'from-emerald-400 to-emerald-600', 'from-pink-400 to-pink-600'];
                                    const textColors = ['text-sky-500', 'text-purple-500', 'text-amber-500', 'text-emerald-500', 'text-pink-500'];
                                    const bgColors = ['bg-sky-500/5', 'bg-purple-500/5', 'bg-amber-500/5', 'bg-emerald-500/5', 'bg-pink-500/5'];
                                    const borderColors = ['border-sky-500/20', 'border-purple-500/20', 'border-amber-500/20', 'border-emerald-500/20', 'border-pink-500/20'];

                                    const pct = Math.round(p.probability * 100);
                                    const colorIdx = i % barColors.length;

                                    return (
                                        <div key={i} className={`p-4 sm:p-5 rounded-xl border transition-all duration-300 hover:shadow-md ${bgColors[colorIdx]} ${borderColors[colorIdx]} bg-opacity-50 dark:bg-opacity-10 dark:bg-black/20`}>
                                            <div className="flex justify-between items-center mb-3">
                                                <span className="text-[15px] font-bold text-[var(--text-primary)]">{p.disease}</span>
                                                <span className={`text-[16px] font-extrabold ${textColors[colorIdx]}`}>{pct}%</span>
                                            </div>
                                            <div className="w-full h-2.5 rounded-full bg-black/5 dark:bg-white/5 overflow-hidden shadow-inner">
                                                <div
                                                    className={`h-full rounded-full bg-gradient-to-r ${barColors[colorIdx]} transition-all duration-1000 ease-out`}
                                                    style={{ width: `${pct}%` }}
                                                />
                                            </div>
                                            <div className="text-[11px] font-bold text-[var(--text-muted)] mt-2.5 uppercase tracking-wider">
                                                Model Confidence: {(p.confidence * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Recommended Tests */}
                        {tests.length > 0 && (
                            <div className={cardClasses}>
                                <SectionHeader icon="🧪" title="Recommended Tests" />
                                <div className="flex flex-wrap gap-2.5">
                                    {tests.map((t, i) => (
                                        <span key={i} className="px-3.5 py-1.5 rounded-lg text-[13px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 shadow-sm">
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* AI Reasoning */}
                        {reasoning.length > 0 && (
                            <div className={cardClasses}>
                                <SectionHeader icon="🧠" title="AI Reasoning Steps" />
                                <div className="space-y-3">
                                    {reasoning.map((step, i) => (
                                        <div key={i} className="flex gap-4 p-4 rounded-xl bg-[var(--bg-body)] border border-[var(--border-glass)] shadow-sm hover:border-purple-500/30 transition-colors">
                                            <div className="flex w-7 h-7 flex-shrink-0 items-center justify-center rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 font-bold text-[14px] shadow-sm">
                                                {step.step_number}
                                            </div>
                                            <div className="flex-1 min-w-0 pt-0.5">
                                                <div className="text-[14px] font-medium text-[var(--text-primary)] leading-relaxed">{step.description}</div>
                                                <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-2.5">
                                                    <span className="text-[11px] px-2 py-0.5 rounded bg-[var(--bg-glass)] border border-[var(--border-glass)] text-[var(--text-muted)] font-medium">
                                                        Evidence: <span className="text-[var(--text-secondary)]">{step.evidence}</span>
                                                    </span>
                                                    <span className="text-[11px] px-2 py-0.5 rounded bg-sky-500/10 border border-sky-500/20 text-sky-600 dark:text-sky-400 font-bold">
                                                        {(step.confidence * 100).toFixed(0)}% conf
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* AI Explanation */}
                        {explanation && (
                            <div className={cardClasses}>
                                <SectionHeader icon="💡" title="AI Explanation" />
                                <p className="text-[14px] font-medium text-[var(--text-secondary)] leading-loose m-0">{explanation}</p>
                            </div>
                        )}

                        {/* Disclaimer */}
                        <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/10 flex items-start gap-3">
                            <span className="text-lg opacity-80 mt-0.5">⚠️</span>
                            <p className="text-[13px] font-medium text-red-600 dark:text-red-400/80 leading-relaxed m-0">
                                <strong>Disclaimer:</strong> AI-assisted analysis only. Always consult a qualified healthcare professional for diagnosis.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
