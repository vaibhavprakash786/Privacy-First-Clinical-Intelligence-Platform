'use client';
import { useState } from 'react';
import { styles } from '@/lib/styles';
import { getRecords, getTrends, getPatientAISummary } from '@/lib/api';

const SEVERITY_COLORS: Record<string, { bg: string; color: string; label: string }> = {
    critical: { bg: 'rgba(239,68,68,0.15)', color: '#ef4444', label: '🔴 CRITICAL' },
    elevated: { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', label: '🟡 ELEVATED' },
    normal: { bg: 'rgba(34,197,94,0.1)', color: '#22c55e', label: '🟢 NORMAL' },
};

const VITAL_LABELS: Record<string, { label: string; unit: string; normalLow: number; normalHigh: number; criticalLow: number; criticalHigh: number }> = {
    blood_pressure_systolic: { label: 'Systolic BP', unit: 'mmHg', normalLow: 90, normalHigh: 130, criticalLow: 70, criticalHigh: 180 },
    blood_pressure_diastolic: { label: 'Diastolic BP', unit: 'mmHg', normalLow: 60, normalHigh: 85, criticalLow: 40, criticalHigh: 120 },
    heart_rate: { label: 'Heart Rate', unit: 'bpm', normalLow: 60, normalHigh: 100, criticalLow: 40, criticalHigh: 150 },
    temperature: { label: 'Temp', unit: '°C', normalLow: 36.1, normalHigh: 37.5, criticalLow: 35, criticalHigh: 39.5 },
    oxygen_saturation: { label: 'SpO₂', unit: '%', normalLow: 95, normalHigh: 100, criticalLow: 90, criticalHigh: 100 },
    respiratory_rate: { label: 'Resp Rate', unit: 'br/min', normalLow: 12, normalHigh: 20, criticalLow: 8, criticalHigh: 30 },
    blood_glucose: { label: 'Glucose', unit: 'mg/dL', normalLow: 70, normalHigh: 140, criticalLow: 50, criticalHigh: 300 },
    weight: { label: 'Weight', unit: 'kg', normalLow: 30, normalHigh: 120, criticalLow: 20, criticalHigh: 200 },
};

function getVitalSeverity(key: string, value: number): 'critical' | 'elevated' | 'normal' {
    const def = VITAL_LABELS[key];
    if (!def) return 'normal';
    if (value <= def.criticalLow || value >= def.criticalHigh) return 'critical';
    if (value < def.normalLow || value > def.normalHigh) return 'elevated';
    return 'normal';
}

export default function RecordsPage() {
    const [patientId, setPatientId] = useState('');
    const [records, setRecords] = useState<any[]>([]);
    const [trends, setTrends] = useState<any[]>([]);
    const [aiSummary, setAiSummary] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

    const handleSearch = async () => {
        if (!patientId.trim()) return;
        setLoading(true);
        setHasSearched(true);
        setAiSummary(null); // Reset summary on new search
        try {
            const [recRes, trendRes] = await Promise.all([getRecords(patientId), getTrends(patientId)]);
            setRecords(recRes.data || []);
            setTrends(trendRes.data || []);
        } catch {
            setRecords([]);
            setTrends([]);
        }
        setLoading(false);
    };

    const fetchAiSummary = async () => {
        if (!patientId.trim() || records.length === 0) return;
        setAiLoading(true);
        try {
            const res = await getPatientAISummary(patientId);
            setAiSummary(res.data);
        } catch (e) {
            console.error('Failed to fetch AI summary', e);
        }
        setAiLoading(false);
    };

    return (
        <main style={styles.mainContent}>
            <h1 style={styles.pageTitle}>🔒 Medical Records</h1>
            <p style={styles.pageSubtitle}>EHR-style privacy-masked records · All PII/PHI redacted via MS Presidio DataGuard</p>

            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                <input placeholder="Enter Patient ID (e.g., VM-ABC123)" value={patientId}
                    onChange={e => setPatientId(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()}
                    style={{ ...styles.inputField, flex: 1, boxSizing: 'border-box' as const }} />
                <button onClick={handleSearch} disabled={loading} style={styles.btnPrimary}>
                    {loading ? 'Loading...' : '🔍 View Records'}
                </button>
            </div>

            {/* Privacy banner */}
            <div style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.15)', borderRadius: '10px', padding: '10px 16px', marginBottom: '20px' }}>
                <p style={{ color: 'rgba(234,179,8,0.9)', fontSize: '12px', margin: 0 }}>
                    🔐 <strong>DataGuard Privacy Active:</strong> Names, Aadhaar, PAN, phone, email, and addresses are automatically masked with [REDACTED] tokens. Original data is never exposed.
                </p>
            </div>

            {/* AI Summary Section */}
            {hasSearched && records.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <h3 style={{ color: '#22d3ee', margin: 0, fontSize: '15px', fontWeight: 700 }}>✨ AI Clinical Summary</h3>
                        {!aiSummary && (
                            <button onClick={fetchAiSummary} disabled={aiLoading} style={{ ...styles.btnPrimary, padding: '6px 12px', fontSize: '12px' }}>
                                {aiLoading ? 'Generating...' : 'Generate AI Summary'}
                            </button>
                        )}
                    </div>

                    {aiSummary && (
                        <div style={{ ...styles.glassCard, padding: '16px', border: '1px solid rgba(34,211,238,0.2)' }}>
                            {aiSummary.from_cache && (
                                <div style={{ fontSize: '10px', color: '#22c55e', marginBottom: '8px', fontWeight: 600 }}>⚡ Loaded from Cache</div>
                            )}
                            <div style={{ marginBottom: '14px' }}>
                                <div style={{ fontSize: '11px', color: 'rgba(34,211,238,0.8)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px', fontWeight: 700 }}>Overall Assessment</div>
                                <p style={{ fontSize: '14px', color: 'var(--text-primary)', margin: 0, lineHeight: 1.5 }}>{aiSummary.overall_assessment}</p>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '6px', fontWeight: 600 }}>Key Findings</div>
                                    <ul style={{ margin: 0, paddingLeft: '16px', color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.6 }}>
                                        {aiSummary.key_findings?.map((tf: string, i: number) => <li key={i}>{tf}</li>)}
                                    </ul>
                                </div>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '6px', fontWeight: 600 }}>Recommendations</div>
                                    <ul style={{ margin: 0, paddingLeft: '16px', color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.6 }}>
                                        {aiSummary.recommendations?.map((r: string, i: number) => <li key={i}>{r}</li>)}
                                    </ul>
                                </div>
                            </div>

                            <div style={{ marginTop: '14px', paddingTop: '14px', borderTop: '1px solid var(--border-glass)' }}>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px', fontWeight: 600 }}>Medication Review</div>
                                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>{aiSummary.medication_review}</p>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Health Trends */}
            {trends.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ color: '#22d3ee', marginBottom: '10px', fontSize: '15px', fontWeight: 700 }}>📈 Health Trends</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '10px' }}>
                        {trends.map((t: any, i: number) => {
                            const lastVal = t.data_points?.[t.data_points.length - 1]?.value;
                            const trendIcon = t.trend === 'improving' ? '↗' : t.trend === 'worsening' ? '↘' : '→';
                            const trendColor = t.trend === 'improving' ? '#22c55e' : t.trend === 'worsening' ? '#ef4444' : '#94a3b8';

                            // Fluctuation alert
                            let varianceAlert = null;
                            if (t.data_points?.length >= 3) {
                                const vals = t.data_points.map((p: any) => p.value);
                                const max = Math.max(...vals);
                                const min = Math.min(...vals);
                                if ((max - min) / min > 0.15) { // more than 15% fluctuation
                                    varianceAlert = <span style={{ marginLeft: '6px', padding: '2px 6px', background: 'rgba(245,158,11,0.15)', color: '#f59e0b', borderRadius: '4px', fontSize: '9px', fontWeight: 700 }}>⚠️ FLUCTUATING</span>;
                                }
                            }

                            return (
                                <div key={i} style={{ ...styles.glassCard, padding: '14px' }}>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px', display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                                        {t.metric_name}
                                        {varianceAlert}
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                                        <span style={{ fontSize: '24px', fontWeight: 700, color: trendColor }}>{lastVal ?? '—'}</span>
                                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t.unit}</span>
                                    </div>
                                    <div style={{ fontSize: '11px', color: trendColor, marginTop: '2px', fontWeight: 500 }}>{trendIcon} {t.trend}</div>
                                    {t.normal_range && (
                                        <div style={{ fontSize: '10px', color: 'var(--text-muted)', opacity: 0.7, marginTop: '4px' }}>
                                            Normal: {t.normal_range.min}–{t.normal_range.max}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Records (EHR style) */}
            {records.length > 0 ? (
                <div>
                    <h3 style={{ color: '#22d3ee', marginBottom: '10px', fontSize: '15px', fontWeight: 700 }}>📋 Encounter History ({records.length} visits)</h3>
                    {records.map((r: any, i: number) => {
                        const isExpanded = expandedIdx === i;
                        // Use backend severity if available, otherwise fallback
                        const severity = SEVERITY_COLORS[r.severity || 'normal'] || SEVERITY_COLORS.normal;
                        const prevRecord = i < records.length - 1 ? records[i + 1] : null;

                        return (
                            <div key={i} onClick={() => setExpandedIdx(isExpanded ? null : i)}
                                style={{ ...styles.glassCard, marginBottom: '10px', cursor: 'pointer', transition: 'all 0.15s', borderLeft: `3px solid ${severity.color}` }}>

                                {/* Header */}
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: isExpanded ? '14px' : 0 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <div>
                                            <span style={{ color: '#22d3ee', fontWeight: 700, fontSize: '14px' }}>{r.visit_type}</span>
                                            {r.department && <span style={{ color: 'rgba(148,163,184,0.4)', fontSize: '12px', marginLeft: '8px' }}>· {r.department}</span>}
                                            {r.doctor_name && <span style={{ color: 'rgba(148,163,184,0.5)', fontSize: '12px', marginLeft: '8px' }}>· Dr. {r.doctor_name}</span>}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                        <span style={{ fontSize: '12px', color: 'rgba(203,213,225,0.5)' }}>{new Date(r.visit_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                                        <span style={{ padding: '3px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: 600, background: severity.bg, color: severity.color }}>{severity.label}</span>
                                        {r.entities_masked > 0 && (
                                            <span style={{ padding: '3px 8px', borderRadius: '6px', fontSize: '10px', background: 'rgba(239,68,68,0.1)', color: '#fca5a5' }}>
                                                🔒 {r.entities_masked} masked
                                            </span>
                                        )}
                                        <span style={{ color: 'rgba(148,163,184,0.4)', fontSize: '16px' }}>{isExpanded ? '▲' : '▼'}</span>
                                    </div>
                                </div>

                                {/* Expanded Content */}
                                {isExpanded && (
                                    <div onClick={e => e.stopPropagation()}>
                                        {/* Vitals Grid with Changes */}
                                        {r.vitals && Object.keys(r.vitals).length > 0 && (
                                            <div style={{ marginBottom: '14px' }}>
                                                <div style={{ fontSize: '11px', color: 'rgba(148,163,184,0.5)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '6px', fontWeight: 600 }}>Vital Signs</div>
                                                <div style={{ display: 'flex', flexWrap: 'wrap' as const, gap: '6px' }}>
                                                    {Object.entries(r.vitals).map(([key, val]) => {
                                                        const vdef = VITAL_LABELS[key];
                                                        const sev = getVitalSeverity(key, val as number);
                                                        const sc = SEVERITY_COLORS[sev];

                                                        // Compare with previous record
                                                        let changeIndicator = null;
                                                        if (prevRecord?.vitals?.[key] !== undefined) {
                                                            const prevVal = prevRecord.vitals[key];
                                                            const diff = (val as number) - prevVal;
                                                            if (Math.abs(diff) > 0) {
                                                                const isIncrease = diff > 0;
                                                                // Simple bad/good color logic for BP/HR/Temp
                                                                let diffColor = 'rgba(148,163,184,0.5)';
                                                                if (key.includes('pressure') || key === 'heart_rate') {
                                                                    diffColor = isIncrease && sev !== 'normal' ? '#ef4444' : '#22c55e';
                                                                }
                                                                changeIndicator = <span style={{ fontSize: '10px', color: diffColor, marginLeft: '4px' }}>{isIncrease ? '↑' : '↓'}{Math.abs(diff)}</span>;
                                                            }
                                                        }

                                                        return (
                                                            <div key={key} style={{ padding: '6px 10px', borderRadius: '8px', background: sc.bg, border: `1px solid ${sc.color}22` }}>
                                                                <div style={{ fontSize: '10px', color: 'rgba(148,163,184,0.5)' }}>{vdef?.label || key}</div>
                                                                <div style={{ fontSize: '15px', fontWeight: 700, color: sc.color }}>
                                                                    {String(val)} <span style={{ fontSize: '10px', fontWeight: 400 }}>{vdef?.unit || ''}</span>
                                                                    {changeIndicator}
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}

                                        {/* Clinical Notes */}
                                        {r.masked_complaint && (
                                            <div style={{ marginBottom: '10px' }}>
                                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '4px', fontWeight: 600 }}>Chief Complaint</div>
                                                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0, lineHeight: 1.5, background: 'var(--bg-card-hover)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>{r.masked_complaint}</p>
                                            </div>
                                        )}
                                        {r.masked_hpi && (
                                            <div style={{ marginBottom: '10px' }}>
                                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '4px', fontWeight: 600 }}>History of Present Illness</div>
                                                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0, lineHeight: 1.5, background: 'var(--bg-card-hover)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>{r.masked_hpi}</p>
                                            </div>
                                        )}
                                        {r.masked_assessment && (
                                            <div style={{ marginBottom: '10px' }}>
                                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '4px', fontWeight: 600 }}>Assessment</div>
                                                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0, lineHeight: 1.5, background: 'var(--bg-card-hover)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>{r.masked_assessment}</p>
                                            </div>
                                        )}
                                        {r.masked_plan && (
                                            <div style={{ marginBottom: '10px' }}>
                                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '4px', fontWeight: 600 }}>Plan</div>
                                                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0, lineHeight: 1.5, background: 'var(--bg-card-hover)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>{r.masked_plan}</p>
                                            </div>
                                        )}

                                        {/* Medications */}
                                        {r.medications_prescribed?.length > 0 && (
                                            <div style={{ marginTop: '14px', marginBottom: '10px' }}>
                                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '6px', fontWeight: 600 }}>Medications Prescribed</div>
                                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '8px' }}>
                                                    {r.medications_prescribed.map((med: any, mi: number) => (
                                                        <div key={mi} style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(34,211,238,0.05)', border: '1px solid rgba(34,211,238,0.15)' }}>
                                                            <div style={{ color: '#22d3ee', fontWeight: 600, fontSize: '13px', marginBottom: '2px' }}>{med.name}</div>
                                                            <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{med.dosage} · {med.frequency}</div>
                                                            {med.duration && <div style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '2px' }}>Duration: {med.duration}</div>}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Diagnosis Tags */}
                                        {r.diagnosis?.length > 0 && (
                                            <div style={{ marginTop: '10px' }}>
                                                <div style={{ fontSize: '11px', color: 'rgba(148,163,184,0.5)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '6px', fontWeight: 600 }}>Diagnosis</div>
                                                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' as const }}>
                                                    {r.diagnosis.map((d: string, di: number) => (
                                                        <span key={di} style={{ ...styles.chip, background: 'rgba(139,92,246,0.12)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.2)' }}>{d}</span>
                                                    ))}
                                                    {r.icd_codes?.map((c: string, ci: number) => (
                                                        <span key={`icd-${ci}`} style={{ ...styles.chip, background: 'rgba(34,211,238,0.08)', color: 'rgba(34,211,238,0.7)', border: '1px solid rgba(34,211,238,0.15)', fontFamily: 'monospace', fontSize: '11px' }}>{c}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Lab Results */}
                                        {r.lab_results?.length > 0 && (
                                            <div style={{ marginTop: '12px' }}>
                                                <div style={{ fontSize: '11px', color: 'rgba(148,163,184,0.5)', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: '6px', fontWeight: 600 }}>Lab Results</div>
                                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '6px' }}>
                                                    {r.lab_results.map((lab: any, li: number) => (
                                                        <div key={li} style={{ padding: '6px 10px', borderRadius: '6px', background: 'rgba(0,0,0,0.15)', fontSize: '12px' }}>
                                                            <span style={{ color: 'rgba(148,163,184,0.5)' }}>{lab.test}:</span>{' '}
                                                            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{lab.value} {lab.unit}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Follow Up */}
                                        {r.follow_up_date && (
                                            <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(34,197,94,0.05)', borderRadius: '6px', borderLeft: '2px solid rgba(34,197,94,0.5)' }}>
                                                <span style={{ fontSize: '11px', color: 'rgba(34,197,94,0.8)', fontWeight: 600, marginRight: '8px' }}>FOLLOW UP:</span>
                                                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{r.follow_up_date}</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            ) : hasSearched && !loading ? (
                <div style={{ ...styles.glassCard, textAlign: 'center' as const, padding: '48px' }}>
                    <p style={{ color: 'rgba(203,213,225,0.5)', fontSize: '16px', margin: '0 0 6px' }}>No records found for <strong>{patientId}</strong></p>
                    <p style={{ color: 'rgba(203,213,225,0.3)', fontSize: '13px', margin: 0 }}>Register the patient first via Patient Management, then submit clinical data</p>
                </div>
            ) : null}
        </main>
    );
}
