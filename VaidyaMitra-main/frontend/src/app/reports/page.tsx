'use client';
import { useState, useRef, type ChangeEvent, type CSSProperties, type ReactNode } from 'react';
import { styles } from '@/lib/styles';
import { simplifyReport, summarizeReport, translateReport, uploadReportFile } from '@/lib/api';

/* ======= Indian language list (comprehensive) ======= */
const LANGUAGES = [
    { code: 'hi', label: 'हिन्दी', english: 'Hindi', script: 'Devanagari' },
    { code: 'bn', label: 'বাংলা', english: 'Bengali', script: 'Bengali' },
    { code: 'ta', label: 'தமிழ்', english: 'Tamil', script: 'Tamil' },
    { code: 'te', label: 'తెలుగు', english: 'Telugu', script: 'Telugu' },
    { code: 'mr', label: 'मराठी', english: 'Marathi', script: 'Devanagari' },
    { code: 'gu', label: 'ગુજરાતી', english: 'Gujarati', script: 'Gujarati' },
    { code: 'kn', label: 'ಕನ್ನಡ', english: 'Kannada', script: 'Kannada' },
    { code: 'ml', label: 'മലയാളം', english: 'Malayalam', script: 'Malayalam' },
    { code: 'pa', label: 'ਪੰਜਾਬੀ', english: 'Punjabi', script: 'Gurmukhi' },
    { code: 'or', label: 'ଓଡ଼ିଆ', english: 'Odia', script: 'Odia' },
    { code: 'as', label: 'অসমীয়া', english: 'Assamese', script: 'Bengali' },
    { code: 'ur', label: 'اردو', english: 'Urdu', script: 'Nastaliq' },
    { code: 'sd', label: 'سنڌي', english: 'Sindhi', script: 'Arabic' },
    { code: 'ne', label: 'नेपाली', english: 'Nepali', script: 'Devanagari' },
    { code: 'sa', label: 'संस्कृतम्', english: 'Sanskrit', script: 'Devanagari' },
];

const SAMPLE_REPORTS = [
    "Patient presents with elevated HbA1c of 8.2%, indicating poor glycemic control. Fasting blood glucose 186 mg/dL. Creatinine within normal range at 1.1 mg/dL. Lipid profile shows elevated LDL cholesterol at 165 mg/dL. Recommend dose adjustment of Metformin to 1000mg BID, add Atorvastatin 20mg at bedtime. Follow-up in 3 months with repeat HbA1c and lipid panel.",
    "ECG reveals sinus tachycardia with heart rate 110 bpm. No ST-segment changes. Echocardiogram shows mild left ventricular hypertrophy with preserved ejection fraction of 55%. Blood pressure 158/94 mmHg suggests uncontrolled hypertension. Start Telmisartan 40mg OD, continue Amlodipine 5mg. Prophylaxis with Ecosprin 75mg OD. Review in 2 weeks.",
    "Complete blood count shows hemoglobin 9.8 g/dL indicating mild anemia. MCV 72 fL suggestive of iron deficiency. Serum ferritin 12 ng/mL (low). TSH 6.8 mIU/L indicating subclinical hypothyroidism. Bilateral knee X-ray shows early osteoarthritis changes. Start Iron supplementation, Thyronorm 25mcg, Shelcal 500mg BID.",
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_FILE_TYPES = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp'];

/* ======= Shared Styles ======= */
const fieldInput: CSSProperties = {
    width: '100%', boxSizing: 'border-box', padding: '10px 14px', borderRadius: '10px',
    color: 'var(--text-input)', background: 'var(--bg-input)', border: '1px solid var(--border-input)',
    outline: 'none', fontSize: '14px', transition: 'border-color 0.2s, background 0.3s, color 0.3s',
};

const tabStyle = (active: boolean): CSSProperties => ({
    padding: '10px 20px', fontSize: '13px', fontWeight: 600, borderRadius: '10px',
    cursor: 'pointer', border: 'none', transition: 'all 0.2s',
    background: active ? 'var(--chip-active-bg)' : 'var(--btn-inactive-bg)',
    color: active ? 'var(--accent-primary)' : 'var(--chip-inactive-text)',
    boxShadow: active ? 'var(--chip-active-border)' : 'var(--chip-inactive-border)',
});

/* =========================================================================
   Sub-components — OUTSIDE main function to prevent cursor loss
   ========================================================================= */

function SectionHeader({ icon, title, subtitle }: { icon: string; title: string; subtitle?: string }) {
    return (
        <div style={{ marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '16px' }}>{icon}</span>
                <h3 style={{ color: 'var(--accent-primary)', fontSize: '15px', fontWeight: 700, margin: 0 }}>{title}</h3>
            </div>
            {subtitle && <p style={{ color: 'var(--label-text)', fontSize: '12px', margin: '4px 0 0 28px' }}>{subtitle}</p>}
        </div>
    );
}

function InfoBanner({ icon, color, bgColor, borderColor, children }: { icon: string; color: string; bgColor: string; borderColor: string; children: ReactNode }) {
    return (
        <div style={{ background: bgColor, border: `1px solid ${borderColor}`, borderRadius: '10px', padding: '10px 16px', marginBottom: '14px' }}>
            <p style={{ color, fontSize: '12px', margin: 0 }}>{icon} {children}</p>
        </div>
    );
}

function ResultCard({ children, style: extraStyle }: { children: ReactNode; style?: CSSProperties }) {
    return <div style={{ ...styles.glassCard, ...extraStyle }}>{children}</div>;
}

/* ======= Main Component ======= */
export default function ReportsPage() {
    const [inputMode, setInputMode] = useState<'text' | 'file'>('text');
    const [reportText, setReportText] = useState('');
    const [simplified, setSimplified] = useState<any>(null);
    const [summary, setSummary] = useState<any>(null);
    const [translated, setTranslated] = useState<any>(null);
    const [targetLang, setTargetLang] = useState('hi');
    const [loading, setLoading] = useState(false);
    const [translateLoading, setTranslateLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'simplify' | 'summarize'>('simplify');
    const [error, setError] = useState('');

    // File upload
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [uploadProgress, setUploadProgress] = useState('');
    const [dragActive, setDragActive] = useState(false);
    const fileRef = useRef<HTMLInputElement>(null);

    /* ── Validate file ── */
    const validateFile = (file: File): string | null => {
        if (file.size > MAX_FILE_SIZE) return `File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max 10MB.`;
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        if (!ACCEPTED_FILE_TYPES.includes(ext)) return `Unsupported format. Use: ${ACCEPTED_FILE_TYPES.join(', ')}`;
        return null;
    };

    /* ── Handle file selection ── */
    const handleFileSelect = (file: File) => {
        const err = validateFile(file);
        if (err) { setError(err); return; }
        setUploadedFile(file);
        setError('');
    };

    /* ── Simplify text report ── */
    const handleSimplifyText = async () => {
        if (!reportText.trim()) { setError('Please enter or paste a medical report'); return; }
        setLoading(true); setError(''); setSimplified(null); setSummary(null); setTranslated(null);
        try {
            const [simpRes, sumRes] = await Promise.all([simplifyReport(reportText), summarizeReport(reportText)]);
            setSimplified(simpRes.data);
            setSummary(sumRes.data);
        } catch (e: any) {
            setError(e.message || 'Processing failed. Check backend connection.');
        }
        setLoading(false);
    };

    /* ── Simplify uploaded file ── */
    const handleSimplifyFile = async () => {
        if (!uploadedFile) { setError('Please upload a file first'); return; }
        setLoading(true); setError(''); setSimplified(null); setSummary(null); setTranslated(null);
        setUploadProgress('Uploading file...');
        try {
            setUploadProgress('Running OCR & DataGuard PII scrubbing...');
            const res = await uploadReportFile(uploadedFile);
            if (res.data?.simplified_report) {
                setSimplified(res.data.simplified_report);
                setSummary(res.data.summary);
                setUploadProgress('');
            } else if (res.data?.scrub_result?.extracted_text) {
                // Image: got extracted text, now simplify it
                setUploadProgress('Simplifying extracted text...');
                const text = res.data.scrub_result.extracted_text;
                const [simpRes, sumRes] = await Promise.all([simplifyReport(text), summarizeReport(text)]);
                setSimplified(simpRes.data);
                setSummary(sumRes.data);
                setUploadProgress('');
            } else {
                setError('Could not extract text from the uploaded file. Try pasting the text instead.');
                setUploadProgress('');
            }
        } catch (e: any) {
            setError(e.message || 'File processing failed');
            setUploadProgress('');
        }
        setLoading(false);
    };

    /* ── Translate to Indian language (Amazon Bedrock powered) ── */
    const handleTranslate = async () => {
        const textToTranslate = simplified?.simplified_text;
        if (!textToTranslate) return;
        setTranslateLoading(true); setTranslated(null);
        try {
            const res = await translateReport(textToTranslate, targetLang);
            setTranslated(res.data);
        } catch (e: any) {
            setError(e.message || 'Translation failed');
        }
        setTranslateLoading(false);
    };

    /* ── Copy to clipboard ── */
    const copyToClipboard = async (text: string) => {
        try { await navigator.clipboard.writeText(text); } catch { /* ignore */ }
    };

    const hasResults = simplified || summary;

    return (
        <main style={styles.mainContent}>
            <h1 style={styles.pageTitle}>📄 Report Simplifier</h1>
            <p style={styles.pageSubtitle}>AI converts complex medical reports to simple language · Translate to any Indian language via Amazon Bedrock</p>

            <div style={{ display: 'grid', gridTemplateColumns: hasResults ? '1fr 1fr' : '1fr', gap: '20px' }}>
                {/* ===== LEFT: Input Panel ===== */}
                <div>
                    {/* Input Mode Selector */}
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                        <button onClick={() => setInputMode('text')} style={tabStyle(inputMode === 'text')}>📝 Paste Text</button>
                        <button onClick={() => setInputMode('file')} style={tabStyle(inputMode === 'file')}>📎 Upload PDF / Image</button>
                    </div>

                    <ResultCard>
                        {inputMode === 'text' ? (
                            <>
                                <SectionHeader icon="📝" title="Enter Medical Report" subtitle="Paste Rx, lab report, or discharge summary" />
                                <textarea
                                    id="report-text-input"
                                    value={reportText}
                                    onChange={e => setReportText(e.target.value)}
                                    placeholder="Paste your medical report, lab test results, discharge summary, or doctor's prescription here..."
                                    style={{
                                        ...fieldInput,
                                        minHeight: '220px',
                                        resize: 'vertical' as const,
                                        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                        fontSize: '13px',
                                        lineHeight: 1.7,
                                    }}
                                />
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                                    <span style={{ fontSize: '11px', color: 'rgba(148,163,184,0.3)' }}>
                                        {reportText.length > 0 ? `${reportText.split(/\s+/).filter(Boolean).length} words · ${reportText.length} chars` : 'Min 20 characters'}
                                    </span>
                                    {reportText.length > 0 && (
                                        <button onClick={() => setReportText('')} style={{ background: 'none', border: 'none', color: 'rgba(239,68,68,0.5)', cursor: 'pointer', fontSize: '12px' }}>
                                            ✕ Clear
                                        </button>
                                    )}
                                </div>
                                <button
                                    id="btn-simplify"
                                    onClick={handleSimplifyText}
                                    disabled={loading || reportText.trim().length < 20}
                                    style={{
                                        ...styles.btnPrimary, width: '100%', marginTop: '12px',
                                        opacity: loading || reportText.trim().length < 20 ? 0.5 : 1,
                                        padding: '14px', fontSize: '15px',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                                    }}
                                >
                                    {loading ? '⏳ Analyzing Report...' : '✨ Simplify & Analyze'}
                                </button>
                            </>
                        ) : (
                            <>
                                <SectionHeader icon="📎" title="Upload Medical Document" subtitle="PDF, JPG, PNG, BMP — Max 10MB" />

                                {/* Drop Zone */}
                                <div
                                    onClick={() => fileRef.current?.click()}
                                    onDragOver={e => { e.preventDefault(); setDragActive(true); }}
                                    onDragLeave={() => setDragActive(false)}
                                    onDrop={e => { e.preventDefault(); setDragActive(false); const f = e.dataTransfer.files[0]; if (f) handleFileSelect(f); }}
                                    style={{
                                        border: `2px dashed ${dragActive ? 'rgba(34,211,238,0.6)' : uploadedFile ? 'rgba(34,197,94,0.3)' : 'rgba(56,189,248,0.15)'}`,
                                        borderRadius: '14px', padding: '32px 20px', textAlign: 'center' as const,
                                        cursor: 'pointer', transition: 'all 0.3s',
                                        background: dragActive ? 'rgba(34,211,238,0.03)' : uploadedFile ? 'rgba(34,197,94,0.02)' : 'transparent',
                                    }}
                                >
                                    <input
                                        ref={fileRef}
                                        type="file"
                                        accept=".pdf,.jpg,.jpeg,.png,.bmp"
                                        style={{ display: 'none' }}
                                        onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
                                    />
                                    <div style={{ fontSize: '40px', marginBottom: '8px' }}>
                                        {uploadedFile ? '✅' : dragActive ? '📥' : '📄'}
                                    </div>
                                    {uploadedFile ? (
                                        <div>
                                            <div style={{ color: '#22c55e', fontWeight: 600, fontSize: '14px' }}>{uploadedFile.name}</div>
                                            <div style={{ color: 'rgba(148,163,184,0.4)', fontSize: '12px', marginTop: '4px' }}>
                                                {(uploadedFile.size / 1024).toFixed(0)} KB · Click to change
                                            </div>
                                        </div>
                                    ) : (
                                        <div>
                                            <div style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '14px' }}>
                                                {dragActive ? 'Drop your file here' : 'Drag & drop or click to upload'}
                                            </div>
                                            <div style={{ color: 'rgba(148,163,184,0.4)', fontSize: '12px', marginTop: '4px' }}>
                                                Supports: PDF, JPG, PNG, BMP · Max 10MB
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {uploadProgress && (
                                    <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <div style={{ width: '16px', height: '16px', border: '2px solid rgba(34,211,238,0.3)', borderTop: '2px solid #22d3ee', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                                        <span style={{ fontSize: '13px', color: 'rgba(34,211,238,0.8)' }}>{uploadProgress}</span>
                                    </div>
                                )}

                                <InfoBanner icon="🔐" color="rgba(234,179,8,0.9)" bgColor="rgba(234,179,8,0.06)" borderColor="rgba(234,179,8,0.15)">
                                    <strong>DataGuard:</strong> All uploaded files pass through OCR + PII/PHI scrubbing before AI analysis. No raw patient data reaches AI models.
                                </InfoBanner>

                                <button
                                    id="btn-simplify-file"
                                    onClick={handleSimplifyFile}
                                    disabled={loading || !uploadedFile}
                                    style={{
                                        ...styles.btnPrimary, width: '100%', marginTop: '4px',
                                        opacity: loading || !uploadedFile ? 0.5 : 1,
                                        padding: '14px', fontSize: '15px',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                                    }}
                                >
                                    {loading ? '⏳ Processing Document...' : '✨ Extract & Simplify'}
                                </button>
                            </>
                        )}
                    </ResultCard>

                    {/* Sample Reports */}
                    <ResultCard style={{ marginTop: '16px' }}>
                        <SectionHeader icon="📋" title="Sample Reports" subtitle="Click to load a sample medical report" />
                        <div style={{ display: 'flex', flexDirection: 'column' as const, gap: '8px' }}>
                            {SAMPLE_REPORTS.map((s, i) => (
                                <button
                                    key={i}
                                    onClick={() => { setReportText(s); setInputMode('text'); }}
                                    style={{
                                        background: 'var(--bg-input)', border: '1px solid var(--border-input)',
                                        borderRadius: '10px', padding: '10px 14px', cursor: 'pointer',
                                        textAlign: 'left' as const, color: 'var(--text-secondary)', fontSize: '13px',
                                        lineHeight: 1.6, transition: 'all 0.2s',
                                    }}
                                >
                                    <span style={{ color: 'var(--accent-primary)', fontWeight: 600, fontSize: '11px', textTransform: 'uppercase' as const }}>
                                        Sample {i + 1}:
                                    </span>{' '}
                                    {s.substring(0, 120)}...
                                </button>
                            ))}
                        </div>
                    </ResultCard>

                    {/* Error */}
                    {error && (
                        <div style={{ marginTop: '12px', background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '10px', padding: '10px 14px' }}>
                            <p style={{ color: '#ef4444', fontSize: '13px', margin: 0 }}>❌ {error}</p>
                        </div>
                    )}
                </div>

                {/* ===== RIGHT: Results Panel ===== */}
                {hasResults && (
                    <div>
                        {/* Severity Badge */}
                        {simplified?.severity_assessment && (
                            <div style={{
                                ...styles.glassCard, marginBottom: '14px', padding: '12px 16px',
                                background: `${simplified.severity_assessment.color}08`,
                                border: `1px solid ${simplified.severity_assessment.color}25`,
                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            }}>
                                <span style={{ fontSize: '14px', fontWeight: 700, color: simplified.severity_assessment.color }}>
                                    {simplified.severity_assessment.level === 'HIGH' ? '🔴' : simplified.severity_assessment.level === 'MEDIUM' ? '🟡' : '🟢'}{' '}
                                    {simplified.severity_assessment.label}
                                </span>
                                <span style={{ fontSize: '11px', color: 'rgba(148,163,184,0.4)' }}>AI Severity Assessment</span>
                            </div>
                        )}

                        {/* Result Tabs */}
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
                            <button onClick={() => setActiveTab('simplify')} style={tabStyle(activeTab === 'simplify')}>✨ Simplified</button>
                            <button onClick={() => setActiveTab('summarize')} style={tabStyle(activeTab === 'summarize')}>📊 Summary</button>
                        </div>

                        {/* Simplified Tab */}
                        {activeTab === 'simplify' && simplified && (
                            <ResultCard>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                                    <h4 style={{ color: '#22d3ee', fontSize: '14px', margin: 0 }}>✨ Simplified Report</h4>
                                    <button
                                        onClick={() => copyToClipboard(simplified.simplified_text)}
                                        style={{ background: 'rgba(34,211,238,0.08)', border: '1px solid rgba(34,211,238,0.15)', borderRadius: '8px', padding: '4px 10px', cursor: 'pointer', color: 'rgba(34,211,238,0.7)', fontSize: '11px' }}
                                    >
                                        📋 Copy
                                    </button>
                                </div>
                                <p style={{ color: 'var(--text-primary)', fontSize: '15px', lineHeight: 1.9, margin: 0 }}>
                                    {simplified.simplified_text}
                                </p>

                                {/* Medical Terms Explained */}
                                {simplified.terms_explained?.length > 0 && (
                                    <div style={{ marginTop: '18px', borderTop: '1px solid rgba(56,189,248,0.08)', paddingTop: '14px' }}>
                                        <h4 style={{ color: '#f59e0b', fontSize: '13px', marginBottom: '10px', fontWeight: 700 }}>📖 Medical Terms Explained</h4>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                            {simplified.terms_explained.map((t: any, i: number) => (
                                                <div key={i} style={{
                                                    background: 'var(--bg-input)', border: '1px solid var(--border-input)',
                                                    borderRadius: '8px', padding: '8px 12px',
                                                }}>
                                                    <div style={{ color: '#f59e0b', fontWeight: 600, fontSize: '13px' }}>{t.medical_term}</div>
                                                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '2px' }}>{t.simple_meaning}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </ResultCard>
                        )}

                        {/* Summary Tab */}
                        {activeTab === 'summarize' && summary && (
                            <ResultCard>
                                <h4 style={{ color: '#22d3ee', fontSize: '14px', margin: '0 0 12px' }}>📊 Report Summary</h4>
                                <p style={{ color: 'var(--text-primary)', fontSize: '15px', lineHeight: 1.8, margin: '0 0 14px' }}>
                                    {summary.summary?.overview}
                                </p>

                                {summary.summary?.key_findings?.length > 0 && (
                                    <div style={{ marginBottom: '14px' }}>
                                        <h5 style={{ color: '#22c55e', fontSize: '12px', fontWeight: 700, marginBottom: '8px', textTransform: 'uppercase' as const, letterSpacing: '0.05em' }}>Key Findings</h5>
                                        {summary.summary.key_findings.map((f: string, i: number) => (
                                            <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', marginBottom: '6px' }}>
                                                <span style={{ color: '#22c55e', fontSize: '14px' }}>✓</span>
                                                <span style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.6 }}>{f}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {summary.summary?.next_steps?.length > 0 && (
                                    <div style={{ borderTop: '1px solid rgba(56,189,248,0.08)', paddingTop: '12px' }}>
                                        <h5 style={{ color: '#3b82f6', fontSize: '12px', fontWeight: 700, marginBottom: '8px', textTransform: 'uppercase' as const, letterSpacing: '0.05em' }}>Action Items</h5>
                                        {summary.summary.next_steps.map((s: string, i: number) => (
                                            <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', marginBottom: '6px' }}>
                                                <span style={{ color: '#3b82f6' }}>→</span>
                                                <span style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.6 }}>{s}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </ResultCard>
                        )}

                        {/* ===== Translation Panel ===== */}
                        <ResultCard style={{ marginTop: '16px' }}>
                            <SectionHeader icon="🌐" title="Translate to Indian Language" subtitle="Powered by Amazon Bedrock · Medically accurate multilingual translation" />

                            <InfoBanner icon="ℹ️" color="rgba(34,211,238,0.7)" bgColor="rgba(34,211,238,0.03)" borderColor="rgba(34,211,238,0.1)">
                                Translation uses <strong>Amazon Bedrock</strong>&apos;s medical NLP pipeline for accurate, contextual Indian language translation — preserving medical terminology and meaning.
                            </InfoBanner>

                            {/* Language Grid */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginBottom: '14px' }}>
                                {LANGUAGES.map(l => (
                                    <button
                                        key={l.code}
                                        onClick={() => setTargetLang(l.code)}
                                        style={{
                                            padding: '8px 10px', borderRadius: '8px', cursor: 'pointer', border: 'none',
                                            transition: 'all 0.2s', textAlign: 'left' as const,
                                            background: targetLang === l.code ? 'var(--chip-active-bg)' : 'var(--bg-input)',
                                            boxShadow: targetLang === l.code ? 'var(--chip-active-border)' : 'var(--chip-inactive-border)',
                                        }}
                                    >
                                        <div style={{ color: targetLang === l.code ? 'var(--accent-primary)' : 'var(--text-secondary)', fontSize: '14px', fontWeight: 600 }}>
                                            {l.label}
                                        </div>
                                        <div style={{ color: targetLang === l.code ? 'var(--accent-primary)' : 'var(--text-muted)', fontSize: '11px', opacity: targetLang === l.code ? 0.8 : 0.5 }}>
                                            {l.english} · {l.script}
                                        </div>
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={handleTranslate}
                                disabled={translateLoading || !simplified?.simplified_text}
                                style={{
                                    ...styles.btnPrimary, width: '100%',
                                    opacity: translateLoading || !simplified?.simplified_text ? 0.5 : 1,
                                    padding: '12px', fontSize: '14px',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                                }}
                            >
                                {translateLoading ? '⏳ Translating...' : `🌐 Translate to ${LANGUAGES.find(l => l.code === targetLang)?.english || 'Hindi'}`}
                            </button>

                            {/* Translation Output */}
                            {translated && (
                                <div style={{ marginTop: '14px', padding: '16px', borderRadius: '12px', background: 'rgba(34,211,238,0.03)', border: '1px solid rgba(34,211,238,0.12)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                        <div>
                                            <span style={{ color: '#22d3ee', fontWeight: 700, fontSize: '14px' }}>
                                                {translated.target_native_name || LANGUAGES.find(l => l.code === targetLang)?.label}
                                            </span>
                                            <span style={{ color: 'rgba(148,163,184,0.4)', fontSize: '11px', marginLeft: '8px' }}>
                                                {translated.target_language_name || LANGUAGES.find(l => l.code === targetLang)?.english}
                                            </span>
                                        </div>
                                        <button
                                            onClick={() => copyToClipboard(translated.translated_text)}
                                            style={{ background: 'rgba(34,211,238,0.08)', border: '1px solid rgba(34,211,238,0.15)', borderRadius: '8px', padding: '4px 10px', cursor: 'pointer', color: 'rgba(34,211,238,0.7)', fontSize: '11px' }}
                                        >
                                            📋 Copy
                                        </button>
                                    </div>
                                    <p style={{ color: 'var(--text-primary)', fontSize: '16px', lineHeight: 2.0, margin: 0, whiteSpace: 'pre-wrap' as const }}>
                                        {translated.translated_text}
                                    </p>
                                    <div style={{ marginTop: '10px', fontSize: '10px', color: 'rgba(148,163,184,0.3)' }}>
                                        Translation model: Amazon Bedrock · Medical NLP Pipeline · {translated.model || 'Claude 3'}
                                    </div>
                                </div>
                            )}
                        </ResultCard>
                    </div>
                )}
            </div>

            {/* Disclaimer */}
            <div style={{ marginTop: '24px', padding: '12px 16px', borderRadius: '10px', background: 'rgba(239,68,68,0.04)', border: '1px solid rgba(239,68,68,0.1)' }}>
                <p style={{ fontSize: '12px', color: 'rgba(239,68,68,0.6)', margin: 0 }}>
                    ⚠️ <strong>Disclaimer:</strong> This is AI-simplified analysis. Always consult your healthcare provider for accurate medical interpretation. Translations are AI-generated and may not capture all medical nuances.
                </p>
            </div>

            {/* CSS animation for spinner */}
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </main>
    );
}
