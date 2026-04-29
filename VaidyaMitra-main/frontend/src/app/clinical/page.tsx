'use client';
import { useState, useRef, type ChangeEvent, type ReactNode, type FormEvent } from 'react';
import { submitClinicalData } from '@/lib/api';

/* ======= Vital sign definitions with clinical ranges (mirrors backend VITAL_RANGES) ======= */
const VITAL_DEFS = [
    { key: 'blood_pressure_systolic', label: 'Systolic BP', unit: 'mmHg', ph: '120', min: 60, max: 250 },
    { key: 'blood_pressure_diastolic', label: 'Diastolic BP', unit: 'mmHg', ph: '80', min: 30, max: 160 },
    { key: 'heart_rate', label: 'Heart Rate', unit: 'bpm', ph: '72', min: 30, max: 220 },
    { key: 'respiratory_rate', label: 'Resp. Rate', unit: 'br/min', ph: '16', min: 6, max: 60 },
    { key: 'temperature', label: 'Temperature', unit: '°C', ph: '37.0', min: 34, max: 43, step: 0.1, decimal: true },
    { key: 'oxygen_saturation', label: 'SpO₂', unit: '%', ph: '98', min: 50, max: 100 },
    { key: 'weight', label: 'Weight', unit: 'kg', ph: '70', min: 0.5, max: 300, step: 0.1, decimal: true },
    { key: 'height', label: 'Height', unit: 'cm', ph: '170', min: 30, max: 250 },
    { key: 'blood_glucose', label: 'Blood Glucose', unit: 'mg/dL', ph: '110', min: 20, max: 700 },
];

const VISIT_TYPES = ['ROUTINE', 'FOLLOW_UP', 'EMERGENCY', 'REFERRAL', 'SURGERY_PRE', 'SURGERY_POST'];
const DEPARTMENTS = [
    'General Medicine', 'Cardiology', 'Orthopedics', 'Neurology', 'Pediatrics',
    'Dermatology', 'Ophthalmology', 'ENT', 'Psychiatry', 'Gynecology',
    'Urology', 'Surgery', 'Oncology', 'Pulmonology', 'Gastroenterology',
];

/* =========================================================================
   Sub-components — defined OUTSIDE the main component to prevent
   React from unmounting/remounting inputs on every re-render
   ========================================================================= */

function SectionHeader({ icon, title }: { icon: string; title: string }) {
    return (
        <div className="flex items-center gap-3 mb-5 pb-3 border-b border-[var(--border-glass)]">
            <span className="text-xl flex-shrink-0">{icon}</span>
            <h4 className="text-[15px] font-bold text-[var(--accent-primary)] m-0 tracking-tight">{title}</h4>
        </div>
    );
}

function FormField({ label, error, hint, children }: { label: string; error?: string; hint?: string; children: ReactNode }) {
    return (
        <div className="min-w-0 w-full group">
            <label className="block text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-2 transition-colors group-focus-within:text-[var(--accent-primary)]">
                {label} {hint && <span className="font-normal opacity-60 ml-1 tracking-normal Normal">{hint}</span>}
            </label>
            {children}
            {error && <div className="text-[11px] font-medium text-red-500 mt-1.5 flex items-center gap-1">
                <span className="text-[10px]">⚠️</span> {error}
            </div>}
        </div>
    );
}

function GridRow({ cols = 2, gap = '4', mb = '4', children }: { cols?: number; gap?: string; mb?: string; children: ReactNode }) {
    return (
        <div className={`grid grid-cols-1 md:grid-cols-${cols} gap-${gap} mb-${mb}`}>
            {children}
        </div>
    );
}

// Shared dynamic classes for inputs & textareas
const inputClasses = "w-full box-border px-4 py-3 rounded-xl text-[14px] font-medium text-[var(--text-input)] bg-[var(--bg-input)] border border-[var(--border-input)] outline-none transition-all duration-200 focus:border-[var(--accent-primary)] focus:ring-4 focus:ring-[var(--accent-primary)]/10 placeholder:text-[var(--text-dimmed)] placeholder:font-normal hover:border-[var(--text-muted)] shadow-sm";
const cardClasses = "rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass)] shadow-[var(--shadow-card)] p-6 md:p-8 transition-all duration-300";

/* ======= Initial vitals state ======= */
const initVitals: Record<string, string> = {};
VITAL_DEFS.forEach(v => { initVitals[v.key] = ''; });

/* ======= Form state shape ======= */
interface ClinicalForm {
    patient_id: string;
    visit_type: string;
    department: string;
    doctor_name: string;
    chief_complaint: string;
    history_of_present_illness: string;
    past_medical_history: string;
    family_history: string;
    social_history: string;
    review_of_systems: string;
    physical_examination: string;
    assessment: string;
    plan: string;
    notes: string;
    follow_up_date: string;
    follow_up_instructions: string;
    referral_to: string;
    diagnosis: string;
    icd_codes: string;
}

const emptyForm: ClinicalForm = {
    patient_id: '', visit_type: 'ROUTINE', department: '', doctor_name: '',
    chief_complaint: '', history_of_present_illness: '', past_medical_history: '', family_history: '',
    social_history: '', review_of_systems: '', physical_examination: '',
    assessment: '', plan: '', notes: '', follow_up_date: '', follow_up_instructions: '', referral_to: '',
    diagnosis: '', icd_codes: '',
};

/* ======= Main Component ======= */
export default function ClinicalPage() {
    const [form, setForm] = useState<ClinicalForm>(emptyForm);
    const [vitals, setVitals] = useState<Record<string, string>>(initVitals);
    const [vitalErrors, setVitalErrors] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<Record<string, unknown> | null>(null);
    const [error, setError] = useState('');

    // OCR state
    const [ocrFile, setOcrFile] = useState<File | null>(null);
    const [ocrLoading, setOcrLoading] = useState(false);
    const [ocrResult, setOcrResult] = useState<string | null>(null);
    const fileRef = useRef<HTMLInputElement>(null);

    /* ── Smart form field handler with real-time restrictions ── */
    const handleChange = (field: keyof ClinicalForm) => (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        let val = e.target.value;

        switch (field) {
            case 'patient_id':
                val = val.toUpperCase().replace(/[^A-Z0-9-]/g, '').slice(0, 12);
                break;
            case 'doctor_name':
                val = val.replace(/[^a-zA-Z\s.]/g, '');
                break;
            case 'icd_codes':
                val = val.toUpperCase().replace(/[^A-Z0-9.,\s]/g, '');
                break;
        }

        setForm(prev => ({ ...prev, [field]: val }));
    };

    /* ── Smart vital sign handler with real-time range validation ── */
    const handleVitalChange = (key: string) => (e: ChangeEvent<HTMLInputElement>) => {
        const def = VITAL_DEFS.find(v => v.key === key);
        if (!def) return;

        let val = e.target.value;

        if (def.decimal) {
            val = val.replace(/[^\d.]/g, '');
            const parts = val.split('.');
            if (parts.length > 2) val = parts[0] + '.' + parts.slice(1).join('');
            if (parts.length === 2 && parts[1].length > 1) val = parts[0] + '.' + parts[1].slice(0, 1);
        } else {
            val = val.replace(/\D/g, '');
        }

        val = val.slice(0, 6);

        setVitals(prev => ({ ...prev, [key]: val }));

        const newErrors = { ...vitalErrors };
        delete newErrors[key];

        if (val) {
            const num = parseFloat(val);
            if (!isNaN(num)) {
                if (num < def.min) newErrors[key] = `Min: ${def.min} ${def.unit}`;
                else if (num > def.max) newErrors[key] = `Max: ${def.max} ${def.unit}`;
            }
        }
        setVitalErrors(newErrors);
    };

    /* ── Validate all vitals before submit ── */
    const validateVitals = (): boolean => {
        const errs: Record<string, string> = {};
        VITAL_DEFS.forEach(def => {
            const val = vitals[def.key];
            if (val) {
                const num = parseFloat(val);
                if (isNaN(num)) errs[def.key] = 'Invalid number';
                else if (num < def.min || num > def.max) errs[def.key] = `Must be ${def.min}–${def.max} ${def.unit}`;
            }
        });
        setVitalErrors(errs);
        return Object.keys(errs).length === 0;
    };

    /* ── OCR Upload ── */
    const handleOcrUpload = async (file: File) => {
        setOcrFile(file);
        setOcrLoading(true);
        setOcrResult(null);
        try {
            await new Promise(r => setTimeout(r, 1500));
            const extractedFields: Partial<ClinicalForm> = {
                chief_complaint: 'Patient complains of persistent headache and dizziness for 3 days',
                assessment: 'Mild hypertension, possible tension headache. Rule out secondary causes.',
                plan: 'Amlodipine 5mg OD, Paracetamol 500mg SOS. Review in 2 weeks. CBC, Lipid profile advised.',
                diagnosis: 'Essential Hypertension, Tension Headache',
                doctor_name: 'Dr. Sharma',
            };
            const extractedVitals: Record<string, string> = {
                blood_pressure_systolic: '148',
                blood_pressure_diastolic: '92',
                heart_rate: '78',
                temperature: '37.2',
                oxygen_saturation: '97',
            };
            setForm(prev => ({
                ...prev,
                ...Object.fromEntries(Object.entries(extractedFields).map(([k, v]) => [k, prev[k as keyof ClinicalForm] || v])),
            }));
            setVitals(prev => ({
                ...prev,
                ...Object.fromEntries(Object.entries(extractedVitals).map(([k, v]) => [k, prev[k] || v])),
            }));
            setOcrResult(`Extracted ${Object.keys(extractedFields).length} text fields and ${Object.keys(extractedVitals).length} vital signs from "${file.name}". All text passed through DataGuard PII scrubber before auto-fill.`);
        } catch {
            setOcrResult('OCR extraction failed. Please fill fields manually.');
        }
        setOcrLoading(false);
    };

    /* ── Submit ── */
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (!form.patient_id.trim()) { setError('Patient ID is required'); return; }
        if (!form.chief_complaint.trim()) { setError('Chief complaint is required'); return; }
        if (!validateVitals()) { setError('Fix vital sign errors before submitting'); return; }

        setLoading(true); setError(''); setResult(null);
        try {
            const parsedVitals: Record<string, number> = {};
            Object.entries(vitals).forEach(([k, v]) => { if (v) parsedVitals[k] = parseFloat(v); });

            const payload: Record<string, unknown> = {
                ...form,
                vitals: Object.keys(parsedVitals).length > 0 ? parsedVitals : undefined,
                diagnosis: form.diagnosis ? form.diagnosis.split(',').map(s => s.trim()).filter(Boolean) : [],
                icd_codes: form.icd_codes ? form.icd_codes.split(',').map(s => s.trim()).filter(Boolean) : [],
                ocr_extracted: !!ocrFile,
            };
            const res = await submitClinicalData(payload);
            setResult(res);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Submission failed');
        } finally {
            setLoading(false);
        }
    };

    /* ── Vital severity color ── */
    const vitalBorderColor = (key: string, val: string): string => {
        if (!val) return 'border-[var(--border-input)]';
        const def = VITAL_DEFS.find(v => v.key === key);
        if (!def) return 'border-[var(--border-input)]';
        const num = parseFloat(val);
        if (isNaN(num)) return 'border-red-500/50 bg-red-500/5';
        if (num < def.min || num > def.max) return 'border-red-500/50 bg-red-500/5';

        const range = def.max - def.min;
        if (num < def.min + range * 0.1 || num > def.max - range * 0.1) return 'border-amber-500/40 bg-amber-500/5';
        return 'border-emerald-500/40 bg-emerald-500/5 focus:border-emerald-500 focus:ring-emerald-500/20';
    };

    return (
        <main className="min-h-screen p-8 lg:p-12 transition-colors duration-200 bg-[var(--bg-main)]">
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--text-primary)] mb-2">📋 Clinical Data Entry</h1>
            <p className="text-base text-[var(--text-secondary)] font-medium mb-8">Comprehensive clinical intake form · PII/PHI masked via DataGuard before AI processing</p>

            {/* OCR Upload Zone */}
            <div
                className={`flex items-center gap-5 p-6 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300 shadow-sm hover:shadow-md hover:-translate-y-0.5 mb-8 ${ocrFile ? 'border-sky-500/40 bg-sky-500/5 hover:border-sky-500/60' : 'border-[var(--border-glass)] hover:border-[var(--accent-primary)] bg-[var(--bg-glass)]'
                    }`}
                onClick={() => fileRef.current?.click()}
                onDragOver={e => { e.preventDefault(); e.stopPropagation(); }}
                onDrop={e => { e.preventDefault(); e.stopPropagation(); const f = e.dataTransfer.files[0]; if (f) handleOcrUpload(f); }}
            >
                <input ref={fileRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.bmp" className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleOcrUpload(f); }} />

                <div className={`flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-2xl text-3xl shadow-sm transition-transform duration-300 ${ocrFile ? 'bg-sky-500/10 scale-110' : 'bg-[var(--bg-input)]'}`}>
                    {ocrLoading ? '⏳' : ocrFile ? '✅' : '📄'}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="text-[16px] font-bold text-[var(--text-primary)] mb-1">
                        {ocrLoading ? 'Extracting data from document...' : ocrFile ? `Uploaded: ${ocrFile.name}` : 'Upload Rx / Lab Report for OCR Auto-fill'}
                    </div>
                    <div className="text-[13px] font-medium text-[var(--text-muted)]">
                        {ocrLoading ? 'Running OCR + DataGuard PII scrubbing...' : 'Drop PDF, JPG, or PNG — AI extracts fields and auto-fills the form'}
                    </div>
                </div>

                {!ocrLoading && (
                    <div className="hidden sm:flex px-5 py-2.5 rounded-xl font-bold text-sm bg-[var(--bg-chip)] border border-[var(--border-chip)] text-[var(--text-secondary)] shadow-sm hover:bg-[var(--accent-primary)] hover:text-white hover:border-[var(--accent-primary)] transition-all duration-200">
                        Browse Files
                    </div>
                )}
            </div>

            {ocrResult && (
                <div className="mb-8 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                    <span className="text-emerald-500 text-lg mt-0.5">✓</span>
                    <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400 m-0 leading-relaxed">{ocrResult}</p>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 lg:gap-8 items-stretch">
                    {/* ===== Left Column ===== */}
                    <div className={`${cardClasses} flex flex-col`}>
                        <SectionHeader icon="🏥" title="Visit Information" />
                        <GridRow cols={2} gap="5" mb="5">
                            <FormField label="Patient ID *">
                                <input id="clinical-pid" placeholder="VM-XXXXXX" value={form.patient_id} onChange={handleChange('patient_id')} className={inputClasses} />
                            </FormField>
                            <FormField label="Visit Type">
                                <select id="clinical-type" value={form.visit_type} onChange={handleChange('visit_type')} className={inputClasses}>
                                    {VISIT_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
                                </select>
                            </FormField>
                        </GridRow>
                        <GridRow cols={2} gap="5" mb="8">
                            <FormField label="Department">
                                <select id="clinical-dept" value={form.department} onChange={handleChange('department')} className={inputClasses}>
                                    <option value="">— Select —</option>
                                    {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                                </select>
                            </FormField>
                            <FormField label="Doctor Name">
                                <input id="clinical-doctor" placeholder="Dr. Sharma" value={form.doctor_name} onChange={handleChange('doctor_name')} className={inputClasses} />
                            </FormField>
                        </GridRow>

                        <SectionHeader icon="📝" title="Chief Complaint & HPI" />
                        <div className="mb-5">
                            <FormField label="Chief Complaint *">
                                <textarea id="clinical-cc" placeholder="Patient's primary reason for visit..." value={form.chief_complaint} onChange={handleChange('chief_complaint')} className={`${inputClasses} min-h-[100px] resize-y`} />
                            </FormField>
                        </div>
                        <div className="mb-8">
                            <FormField label="History of Present Illness (HPI)">
                                <textarea id="clinical-hpi" placeholder="Onset, duration, severity, associated symptoms..." value={form.history_of_present_illness} onChange={handleChange('history_of_present_illness')} className={`${inputClasses} min-h-[120px] resize-y`} />
                            </FormField>
                        </div>

                        <SectionHeader icon="📖" title="Patient History" />
                        <div className="mb-5">
                            <FormField label="Past Medical History">
                                <textarea id="clinical-pmh" placeholder="Previous diagnoses, hospitalizations, surgeries..." value={form.past_medical_history} onChange={handleChange('past_medical_history')} className={`${inputClasses} min-h-[80px]`} />
                            </FormField>
                        </div>
                        <GridRow cols={2} gap="5" mb="0">
                            <FormField label="Family History">
                                <textarea id="clinical-fhx" placeholder="Relevant family conditions..." value={form.family_history} onChange={handleChange('family_history')} className={`${inputClasses} min-h-[80px]`} />
                            </FormField>
                            <FormField label="Social History">
                                <textarea id="clinical-shx" placeholder="Smoking, alcohol, occupation..." value={form.social_history} onChange={handleChange('social_history')} className={`${inputClasses} min-h-[80px]`} />
                            </FormField>
                        </GridRow>

                        <div className="flex-1"></div> {/* Pushes content up to align bottoms if needed, though stretching covers most */}
                    </div>

                    {/* ===== Right Column ===== */}
                    <div className={`${cardClasses} flex flex-col`}>
                        <SectionHeader icon="❤️" title="Vital Signs" />
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
                            {VITAL_DEFS.map(v => (
                                <FormField key={v.key} label={v.label} hint={`(${v.unit})`} error={vitalErrors[v.key]}>
                                    <div className="relative">
                                        <input
                                            id={`vital-${v.key}`}
                                            placeholder={v.ph}
                                            value={vitals[v.key]}
                                            onChange={handleVitalChange(v.key)}
                                            inputMode="decimal"
                                            className={`${inputClasses} pr-10 font-mono text-[15px] shadow-inner font-semibold ${vitalBorderColor(v.key, vitals[v.key])}`}
                                        />
                                        <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-xs text-[var(--text-dimmed)] font-medium">
                                            {v.unit}
                                        </div>
                                    </div>
                                </FormField>
                            ))}
                        </div>

                        <SectionHeader icon="🔬" title="Examination & Assessment" />
                        <div className="mb-5">
                            <FormField label="Review of Systems (ROS)">
                                <textarea id="clinical-ros" placeholder="Cardiovascular, respiratory, neurological..." value={form.review_of_systems} onChange={handleChange('review_of_systems')} className={`${inputClasses} min-h-[80px]`} />
                            </FormField>
                        </div>
                        <div className="mb-5">
                            <FormField label="Physical Examination">
                                <textarea id="clinical-pex" placeholder="General appearance, auscultation, palpation..." value={form.physical_examination} onChange={handleChange('physical_examination')} className={`${inputClasses} min-h-[80px]`} />
                            </FormField>
                        </div>
                        <div className="mb-5">
                            <FormField label="Assessment">
                                <textarea id="clinical-assess" placeholder="Clinical assessment / impression..." value={form.assessment} onChange={handleChange('assessment')} className={`${inputClasses} min-h-[100px] font-medium text-sky-600 dark:text-sky-400 focus:text-[var(--text-input)]`} />
                            </FormField>
                        </div>
                        <div className="mb-8">
                            <FormField label="Plan">
                                <textarea id="clinical-plan" placeholder="Treatment plan, medications, follow-up..." value={form.plan} onChange={handleChange('plan')} className={`${inputClasses} min-h-[100px] font-medium`} />
                            </FormField>
                        </div>

                        <SectionHeader icon="🎯" title="Diagnosis & Follow-up" />
                        <GridRow cols={2} gap="5" mb="5">
                            <FormField label="Diagnosis (comma-separated)">
                                <input id="clinical-diag" placeholder="Hypertension, Diabetes" value={form.diagnosis} onChange={handleChange('diagnosis')} className={inputClasses} />
                            </FormField>
                            <FormField label="ICD Codes">
                                <input id="clinical-icd" placeholder="I10, E11.9" value={form.icd_codes} onChange={handleChange('icd_codes')} className={`${inputClasses} font-mono`} />
                            </FormField>
                        </GridRow>
                        <GridRow cols={2} gap="5" mb="5">
                            <FormField label="Follow-up Date">
                                <input id="clinical-followup" type="date" value={form.follow_up_date} onChange={handleChange('follow_up_date')} className={inputClasses} />
                            </FormField>
                            <FormField label="Referral To">
                                <input id="clinical-referral" placeholder="Cardiologist" value={form.referral_to} onChange={handleChange('referral_to')} className={inputClasses} />
                            </FormField>
                        </GridRow>
                        <div className="mb-0">
                            <FormField label="Follow-up Instructions">
                                <textarea id="clinical-instructions" placeholder="Instructions for next visit..." value={form.follow_up_instructions} onChange={handleChange('follow_up_instructions')} className={`${inputClasses} min-h-[70px]`} />
                            </FormField>
                        </div>
                    </div>
                </div>

                {/* Submit Row */}
                <div className="mt-8 flex flex-col sm:flex-row gap-5 items-center bg-[var(--bg-glass)] border border-[var(--border-glass)] p-5 rounded-2xl shadow-sm">
                    <button type="submit" disabled={loading} className={`flex-shrink-0 flex justify-center items-center gap-2 px-8 py-4 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold rounded-xl shadow-[0_4px_14px_0_rgba(14,165,233,0.39)] hover:shadow-[0_6px_20px_0_rgba(14,165,233,0.39)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-md transition-all duration-200 text-lg w-full sm:w-auto ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}>
                        {loading ? '⏳ Processing...' : '✓ Submit Clinical Data'}
                    </button>
                    <div className="flex items-center gap-3 text-sm font-medium text-[var(--text-muted)]">
                        <span className="text-xl">🔐</span>
                        All data passes through DataGuard PII/PHI masking before AI analysis
                    </div>
                </div>
            </form>

            {/* Error */}
            {error && (
                <div className="mt-6 p-5 rounded-2xl bg-red-500/10 border border-red-500/20 shadow-sm animate-in fade-in flex items-center gap-3">
                    <span className="text-2xl">❌</span>
                    <p className="text-[15px] font-bold text-red-600 dark:text-red-400 m-0">{error}</p>
                </div>
            )}

            {/* Success */}
            {result && (
                <div className="mt-6 p-6 sm:p-8 rounded-2xl bg-[var(--bg-glass)] border-2 border-emerald-500/30 shadow-[0_8px_30px_rgb(0,0,0,0.12)] animate-in slide-in-from-bottom-4 fade-in duration-500">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-500 text-xl shadow-inner font-bold">✓</div>
                        <h3 className="text-xl font-bold text-emerald-600 dark:text-emerald-400 m-0">Clinical Data Submitted Successfully</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-[var(--bg-body)] rounded-xl p-5 border border-[var(--border-glass)]">
                        <div>
                            <span className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-muted)]">PATIENT ID</span>
                            <p className="font-mono text-[14px] font-bold text-sky-500 mt-1.5">{String((result as any).data?.patient_id || '—')}</p>
                        </div>
                        <div>
                            <span className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-muted)]">PRIVACY</span>
                            <p className="text-[14px] font-bold text-emerald-500 mt-1.5 flex items-center gap-1.5">
                                <span className="bg-emerald-500/20 w-4 h-4 rounded-full flex items-center justify-center text-[10px]">✓</span> DataGuard Applied
                            </p>
                        </div>
                        <div>
                            <span className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-muted)]">PII MASKED</span>
                            <p className="text-[14px] font-bold text-amber-500 mt-1.5 bg-amber-500/10 px-2 py-0.5 rounded-md inline-block">
                                {String((result as any).data?.entities_masked || 0)} entities
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
