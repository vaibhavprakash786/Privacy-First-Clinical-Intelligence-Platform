'use client';
import { useState, type ChangeEvent, type CSSProperties, type ReactNode } from 'react';
import { styles } from '@/lib/styles';
import { registerPatient, listPatients, getPatient } from '@/lib/api';

/* ======= Constants ======= */
const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown'];
const GENDERS = [
    { value: 'M', label: 'Male' },
    { value: 'F', label: 'Female' },
    { value: 'O', label: 'Other' },
];
const MARITAL_STATUSES = ['Single', 'Married', 'Widowed', 'Divorced', 'Separated', 'Other'];
const INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa',
    'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala',
    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland',
    'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
    'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Jammu & Kashmir', 'Ladakh',
];
const RELATIONS = ['Spouse', 'Parent', 'Sibling', 'Child', 'Friend', 'Other'];

/* ======= Form state shape ======= */
interface PatientForm {
    name: string;
    age: string;
    gender: string;
    date_of_birth: string;
    blood_group: string;
    marital_status: string;
    phone: string;
    email: string;
    aadhaar_no: string;
    abha_no: string;
    pan_no: string;
    address: string;
    city: string;
    state: string;
    pincode: string;
    emergency_contact_name: string;
    emergency_contact_phone: string;
    emergency_contact_relation: string;
    occupation: string;
    nationality: string;
    allergies: string;
    conditions: string;
    medications: string;
    family_history: string;
    past_surgeries: string;
}

const emptyForm: PatientForm = {
    name: '', age: '', gender: 'M', date_of_birth: '', blood_group: 'Unknown', marital_status: 'Single',
    phone: '', email: '', aadhaar_no: '', abha_no: '', pan_no: '',
    address: '', city: '', state: '', pincode: '',
    emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relation: 'Spouse',
    occupation: '', nationality: 'Indian',
    allergies: '', conditions: '', medications: '', family_history: '', past_surgeries: '',
};

type Errors = Partial<Record<keyof PatientForm, string>>;

/* ======= Validation ======= */
function validate(f: PatientForm): Errors {
    const e: Errors = {};
    if (!f.name.trim()) e.name = 'Full name is required';
    if (!f.age || isNaN(Number(f.age)) || Number(f.age) < 0 || Number(f.age) > 150) e.age = 'Valid age (0-150)';
    if (!f.phone) e.phone = 'Phone number is required';
    else if (!/^[6-9]\d{9}$/.test(f.phone.replace(/\s/g, ''))) e.phone = 'Indian mobile: 10 digits starting with 6-9';
    if (f.email && !/^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(f.email)) e.email = 'Invalid email format';
    if (f.aadhaar_no) {
        const clean = f.aadhaar_no.replace(/[\s-]/g, '');
        if (!/^\d{12}$/.test(clean)) e.aadhaar_no = 'Aadhaar must be 12 digits';
    }
    if (f.abha_no) {
        const clean = f.abha_no.replace(/[\s-]/g, '');
        if (!/^\d{14}$/.test(clean)) e.abha_no = 'ABHA number must be 14 digits';
    }
    if (f.pan_no && !/^[A-Z]{5}[0-9]{4}[A-Z]$/i.test(f.pan_no)) e.pan_no = 'PAN format: ABCDE1234F';
    if (f.pincode && !/^\d{6}$/.test(f.pincode)) e.pincode = 'Pincode must be 6 digits';
    if (f.emergency_contact_phone && !/^[6-9]\d{9}$/.test(f.emergency_contact_phone.replace(/\s/g, ''))) {
        e.emergency_contact_phone = 'Invalid mobile number';
    }
    return e;
}

/* ======= Styles ======= */
const fieldInput: CSSProperties = {
    width: '100%',
    boxSizing: 'border-box',
    padding: '10px 14px',
    borderRadius: '10px',
    color: 'var(--text-input)',
    background: 'var(--bg-input)',
    border: '1px solid var(--border-input)',
    outline: 'none',
    fontSize: '14px',
    transition: 'border-color 0.2s, background 0.3s, color 0.3s',
};

const fieldLabel: CSSProperties = {
    display: 'block',
    fontSize: '11px',
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: '6px',
    fontWeight: 600,
};

const errorText: CSSProperties = { fontSize: '11px', color: '#ef4444', marginTop: '4px' };
const optionalBadge: CSSProperties = { fontSize: '9px', color: 'rgba(148,163,184,0.35)', fontWeight: 400, textTransform: 'none' as const, letterSpacing: 0 };

/* =======================================================================
   IMPORTANT: These sub-components are defined OUTSIDE the main component
   so React does not re-create them on every render (which would cause
   inputs to lose focus after each keystroke).
   ======================================================================= */

function SectionHeader({ icon, title }: { icon: string; title: string }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', paddingBottom: '8px', borderBottom: '1px solid rgba(56,189,248,0.08)' }}>
            <span style={{ fontSize: '16px' }}>{icon}</span>
            <h4 style={{ color: '#22d3ee', fontSize: '14px', fontWeight: 700, margin: 0 }}>{title}</h4>
        </div>
    );
}

function FormField({ label, error, optional, children }: { label: string; error?: string; optional?: boolean; children: ReactNode }) {
    return (
        <div style={{ minWidth: 0 }}>
            <label style={fieldLabel}>
                {label} {optional && <span style={optionalBadge}>(optional)</span>}
            </label>
            {children}
            {error && <div style={errorText}>⚠ {error}</div>}
        </div>
    );
}

function GridRow({ cols = 2, children }: { cols?: number; children: ReactNode }) {
    return (
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: '14px', marginBottom: '14px' }}>
            {children}
        </div>
    );
}

/* ======= Main Component ======= */
export default function PatientsPage() {
    const [activeTab, setActiveTab] = useState<'register' | 'search'>('register');
    const [form, setForm] = useState<PatientForm>(emptyForm);
    const [errors, setErrors] = useState<Errors>({});
    const [searchQuery, setSearchQuery] = useState('');
    const [patients, setPatients] = useState<any[]>([]);
    const [selectedPatient, setSelectedPatient] = useState<any>(null);
    const [registrationResult, setRegistrationResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    /* Smart field change handler with real-time filtering & validation */
    const handleChange = (field: keyof PatientForm) => (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        let val = e.target.value;

        // ── Real-time input restrictions ──
        switch (field) {
            case 'phone':
            case 'emergency_contact_phone':
                val = val.replace(/\D/g, '').slice(0, 10);  // digits only, max 10
                break;
            case 'aadhaar_no':
                val = val.replace(/\D/g, '').slice(0, 12);  // digits only, max 12
                break;
            case 'abha_no':
                val = val.replace(/\D/g, '').slice(0, 14);  // digits only, max 14
                break;
            case 'pincode':
                val = val.replace(/\D/g, '').slice(0, 6);   // digits only, max 6
                break;
            case 'pan_no':
                val = val.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10); // uppercase alphanumeric, max 10
                break;
            case 'age':
                val = val.replace(/\D/g, '').slice(0, 3);   // digits only, max 3
                break;
            case 'name':
                val = val.replace(/[^a-zA-Z\s.]/g, '');     // letters, spaces, dots only
                break;
        }

        setForm(prev => ({ ...prev, [field]: val }));

        // ── Live validation (show error immediately if invalid) ──
        const newErrors = { ...errors };
        delete newErrors[field]; // clear old error first

        switch (field) {
            case 'phone':
                if (val && val.length === 10 && !/^[6-9]/.test(val)) newErrors.phone = 'Must start with 6, 7, 8, or 9';
                else if (val && val.length > 0 && val.length < 10) newErrors.phone = `${val.length}/10 digits`;
                break;
            case 'emergency_contact_phone':
                if (val && val.length === 10 && !/^[6-9]/.test(val)) newErrors.emergency_contact_phone = 'Must start with 6-9';
                else if (val && val.length > 0 && val.length < 10) newErrors.emergency_contact_phone = `${val.length}/10 digits`;
                break;
            case 'aadhaar_no':
                if (val && val.length > 0 && val.length < 12) newErrors.aadhaar_no = `${val.length}/12 digits`;
                break;
            case 'abha_no':
                if (val && val.length > 0 && val.length < 14) newErrors.abha_no = `${val.length}/14 digits`;
                break;
            case 'pincode':
                if (val && val.length > 0 && val.length < 6) newErrors.pincode = `${val.length}/6 digits`;
                break;
            case 'pan_no':
                if (val && val.length === 10 && !/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(val)) newErrors.pan_no = 'Format: ABCDE1234F';
                else if (val && val.length > 0 && val.length < 10) newErrors.pan_no = `${val.length}/10 chars`;
                break;
            case 'email':
                if (val && val.length > 3 && !val.includes('@')) newErrors.email = 'Must contain @';
                break;
            case 'age':
                if (val && (Number(val) < 0 || Number(val) > 150)) newErrors.age = 'Must be 0-150';
                break;
        }

        setErrors(newErrors);
    };

    /* ===== Register ===== */
    const handleRegister = async () => {
        const errs = validate(form);
        setErrors(errs);
        if (Object.keys(errs).length > 0) return;
        setLoading(true);
        try {
            const payload: Record<string, any> = {
                name: form.name.trim(),
                age: parseInt(form.age),
                gender: form.gender,
                blood_group: form.blood_group,
                marital_status: form.marital_status,
                nationality: form.nationality,
                phone: form.phone.replace(/\s/g, ''),
            };
            if (form.date_of_birth) payload.date_of_birth = form.date_of_birth;
            if (form.email) payload.email = form.email.trim();
            if (form.aadhaar_no) payload.aadhaar_no = form.aadhaar_no.replace(/[\s-]/g, '');
            if (form.abha_no) payload.abha_no = form.abha_no.replace(/[\s-]/g, '');
            if (form.pan_no) payload.pan_no = form.pan_no.toUpperCase().trim();
            if (form.address) payload.address = form.address.trim();
            if (form.city) payload.city = form.city.trim();
            if (form.state) payload.state = form.state;
            if (form.pincode) payload.pincode = form.pincode.trim();
            if (form.occupation) payload.occupation = form.occupation.trim();
            if (form.emergency_contact_name) payload.emergency_contact_name = form.emergency_contact_name.trim();
            if (form.emergency_contact_phone) payload.emergency_contact_phone = form.emergency_contact_phone.replace(/\s/g, '');
            if (form.emergency_contact_relation) payload.emergency_contact_relation = form.emergency_contact_relation;
            if (form.allergies) payload.allergies = form.allergies.split(',').map(s => s.trim()).filter(Boolean);
            if (form.conditions) payload.chronic_conditions = form.conditions.split(',').map(s => s.trim()).filter(Boolean);
            if (form.medications) payload.current_medications = form.medications.split(',').map(s => s.trim()).filter(Boolean);
            if (form.family_history) payload.family_history = form.family_history.split(',').map(s => s.trim()).filter(Boolean);
            if (form.past_surgeries) payload.past_surgeries = form.past_surgeries.split(',').map(s => s.trim()).filter(Boolean);

            const res = await registerPatient(payload);
            setRegistrationResult(res.data || res);
            setForm(emptyForm);
        } catch (e: any) {
            setRegistrationResult({ error: e?.response?.data?.detail || e.message || 'Registration failed' });
        }
        setLoading(false);
    };

    /* ===== Search ===== */
    const handleSearch = async () => {
        if (!searchQuery.trim()) return; // Don't search on empty query
        setLoading(true);
        setHasSearched(true);
        try {
            const res = await listPatients(searchQuery);
            setPatients(res.data || []);
        } catch { setPatients([]); }
        setLoading(false);
    };

    const fetchPatientDetails = async (id: string) => {
        try {
            const res = await getPatient(id);
            setSelectedPatient(res.data || res);
        } catch { /* ignore */ }
    };

    return (
        <main style={styles.mainContent}>
            <h1 style={styles.pageTitle}>👤 Patient Management</h1>
            <p style={styles.pageSubtitle}>Hospital-grade registration with Aadhaar, ABHA verification and strict validation</p>

            {/* Tab Switcher */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '22px' }}>
                {(['register', 'search'] as const).map(t => (
                    <button key={t} onClick={() => setActiveTab(t)} style={{
                        padding: '10px 24px', fontSize: '14px', fontWeight: 600, borderRadius: '10px',
                        cursor: 'pointer', border: 'none', transition: 'all 0.2s',
                        background: activeTab === t ? 'rgba(34,211,238,0.2)' : 'rgba(30,41,59,0.4)',
                        color: activeTab === t ? '#22d3ee' : 'rgba(203,213,225,0.7)',
                        boxShadow: activeTab === t ? '0 0 0 1px rgba(34,211,238,0.4)' : '0 0 0 1px rgba(56,189,248,0.08)',
                    }}>
                        {t === 'register' ? '➕ Register Patient' : '🔍 Search Patients'}
                    </button>
                ))}
            </div>

            {/* ========== REGISTER TAB ========== */}
            {activeTab === 'register' && (
                <div style={{ display: 'grid', gridTemplateColumns: registrationResult && !registrationResult.error ? '1.3fr 0.7fr' : '1fr', gap: '20px' }}>
                    <div style={styles.glassCard}>
                        {/* DataGuard Notice */}
                        <div style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.15)', borderRadius: '10px', padding: '10px 16px', marginBottom: '22px' }}>
                            <p style={{ color: 'rgba(234,179,8,0.9)', fontSize: '12px', margin: 0 }}>
                                🔐 <strong>DataGuard Active:</strong> All PII (Aadhaar, ABHA, Phone, Email, PAN) will be encrypted and masked via MS Presidio before any AI processing.
                            </p>
                        </div>

                        {/* Section 1: Personal Information */}
                        <SectionHeader icon="👤" title="Personal Information" />
                        <GridRow cols={3}>
                            <FormField label="Full Name *" error={errors.name}>
                                <input id="patient-name" placeholder="Ravi Kumar" value={form.name} onChange={handleChange('name')} style={fieldInput} />
                            </FormField>
                            <FormField label="Age *" error={errors.age}>
                                <input id="patient-age" type="number" min={0} max={150} placeholder="45" value={form.age} onChange={handleChange('age')} style={fieldInput} />
                            </FormField>
                            <FormField label="Date of Birth" optional>
                                <input id="patient-dob" type="date" value={form.date_of_birth} onChange={handleChange('date_of_birth')} style={fieldInput} />
                            </FormField>
                        </GridRow>
                        <GridRow cols={3}>
                            <FormField label="Gender">
                                <select id="patient-gender" value={form.gender} onChange={handleChange('gender')} style={fieldInput}>
                                    {GENDERS.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
                                </select>
                            </FormField>
                            <FormField label="Blood Group">
                                <select id="patient-blood" value={form.blood_group} onChange={handleChange('blood_group')} style={fieldInput}>
                                    {BLOOD_GROUPS.map(b => <option key={b} value={b}>{b}</option>)}
                                </select>
                            </FormField>
                            <FormField label="Marital Status">
                                <select id="patient-marital" value={form.marital_status} onChange={handleChange('marital_status')} style={fieldInput}>
                                    {MARITAL_STATUSES.map(m => <option key={m} value={m}>{m}</option>)}
                                </select>
                            </FormField>
                        </GridRow>

                        {/* Section 2: Identity & Contact */}
                        <SectionHeader icon="🪪" title="Identity & Contact" />
                        <GridRow cols={3}>
                            <FormField label="Aadhaar Number" error={errors.aadhaar_no} optional>
                                <input id="patient-aadhaar" placeholder="1234 5678 9012" value={form.aadhaar_no} onChange={handleChange('aadhaar_no')} style={fieldInput} autoComplete="off" />
                            </FormField>
                            <FormField label="ABHA Number" error={errors.abha_no} optional>
                                <input id="patient-abha" placeholder="12-3456-7890-1234" value={form.abha_no} onChange={handleChange('abha_no')} style={fieldInput} autoComplete="off" />
                            </FormField>
                            <FormField label="PAN Number" error={errors.pan_no} optional>
                                <input id="patient-pan" placeholder="ABCDE1234F" value={form.pan_no} onChange={handleChange('pan_no')} style={fieldInput} autoComplete="off" />
                            </FormField>
                        </GridRow>
                        <div style={{ background: 'rgba(34,211,238,0.04)', border: '1px solid rgba(34,211,238,0.1)', borderRadius: '8px', padding: '8px 14px', marginBottom: '14px' }}>
                            <p style={{ color: 'rgba(34,211,238,0.7)', fontSize: '11px', margin: 0 }}>
                                ℹ️ <strong>ABHA</strong> (Ayushman Bharat Health Account) is a 14-digit unique health ID under ABDM. It links health records across hospitals. Apply at <strong>abha.abdm.gov.in</strong>
                            </p>
                        </div>
                        <GridRow cols={2}>
                            <FormField label="Mobile Number *" error={errors.phone}>
                                <input id="patient-phone" type="tel" placeholder="9876543210" value={form.phone} onChange={handleChange('phone')} style={fieldInput} autoComplete="tel" />
                            </FormField>
                            <FormField label="Email Address" error={errors.email} optional>
                                <input id="patient-email" type="email" placeholder="ravi@example.com" value={form.email} onChange={handleChange('email')} style={fieldInput} autoComplete="email" />
                            </FormField>
                        </GridRow>

                        {/* Section 3: Address */}
                        <SectionHeader icon="🏠" title="Address" />
                        <div style={{ marginBottom: '14px' }}>
                            <FormField label="Street Address" optional>
                                <input id="patient-address" placeholder="123 MG Road, Block A, Flat 201" value={form.address} onChange={handleChange('address')} style={fieldInput} />
                            </FormField>
                        </div>
                        <GridRow cols={3}>
                            <FormField label="City" optional>
                                <input id="patient-city" placeholder="Mumbai" value={form.city} onChange={handleChange('city')} style={fieldInput} />
                            </FormField>
                            <FormField label="State" optional>
                                <select id="patient-state" value={form.state} onChange={handleChange('state')} style={fieldInput}>
                                    <option value="">— Select State —</option>
                                    {INDIAN_STATES.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                            </FormField>
                            <FormField label="Pincode" error={errors.pincode} optional>
                                <input id="patient-pincode" type="text" inputMode="numeric" placeholder="400001" value={form.pincode} onChange={handleChange('pincode')} style={fieldInput} maxLength={6} />
                            </FormField>
                        </GridRow>

                        {/* Section 4: Emergency Contact */}
                        <SectionHeader icon="🚨" title="Emergency Contact" />
                        <GridRow cols={3}>
                            <FormField label="Contact Name" optional>
                                <input id="ec-name" placeholder="Priya Kumar" value={form.emergency_contact_name} onChange={handleChange('emergency_contact_name')} style={fieldInput} />
                            </FormField>
                            <FormField label="Contact Phone" error={errors.emergency_contact_phone} optional>
                                <input id="ec-phone" type="tel" placeholder="9876543211" value={form.emergency_contact_phone} onChange={handleChange('emergency_contact_phone')} style={fieldInput} />
                            </FormField>
                            <FormField label="Relation" optional>
                                <select id="ec-relation" value={form.emergency_contact_relation} onChange={handleChange('emergency_contact_relation')} style={fieldInput}>
                                    {RELATIONS.map(r => <option key={r} value={r}>{r}</option>)}
                                </select>
                            </FormField>
                        </GridRow>

                        {/* Section 5: Occupation & Medical History */}
                        <SectionHeader icon="🩺" title="Occupation & Medical History" />
                        <GridRow cols={2}>
                            <FormField label="Occupation" optional>
                                <input id="patient-occupation" placeholder="Teacher / Engineer / Farmer" value={form.occupation} onChange={handleChange('occupation')} style={fieldInput} />
                            </FormField>
                            <FormField label="Nationality">
                                <input id="patient-nationality" value={form.nationality} onChange={handleChange('nationality')} style={fieldInput} />
                            </FormField>
                        </GridRow>
                        <div style={{ marginBottom: '14px' }}>
                            <FormField label="Known Allergies" optional>
                                <input id="patient-allergies" placeholder="Penicillin, Sulfa drugs, Dust (comma separated)" value={form.allergies} onChange={handleChange('allergies')} style={fieldInput} />
                            </FormField>
                        </div>
                        <div style={{ marginBottom: '14px' }}>
                            <FormField label="Chronic Conditions" optional>
                                <input id="patient-conditions" placeholder="Diabetes Type 2, Hypertension (comma separated)" value={form.conditions} onChange={handleChange('conditions')} style={fieldInput} />
                            </FormField>
                        </div>
                        <div style={{ marginBottom: '14px' }}>
                            <FormField label="Current Medications" optional>
                                <input id="patient-medications" placeholder="Metformin 500mg, Amlodipine 5mg (comma separated)" value={form.medications} onChange={handleChange('medications')} style={fieldInput} />
                            </FormField>
                        </div>
                        <div style={{ marginBottom: '14px' }}>
                            <FormField label="Family History" optional>
                                <input id="patient-family" placeholder="Father: Diabetes, Mother: Hypertension (comma separated)" value={form.family_history} onChange={handleChange('family_history')} style={fieldInput} />
                            </FormField>
                        </div>
                        <div style={{ marginBottom: '14px' }}>
                            <FormField label="Past Surgeries" optional>
                                <input id="patient-surgeries" placeholder="Appendectomy (2015), Knee Replacement (2020)" value={form.past_surgeries} onChange={handleChange('past_surgeries')} style={fieldInput} />
                            </FormField>
                        </div>

                        {/* Submit */}
                        <button
                            id="btn-register"
                            onClick={handleRegister}
                            disabled={loading}
                            style={{
                                ...styles.btnPrimary, width: '100%', marginTop: '6px',
                                opacity: loading ? 0.6 : 1, display: 'flex',
                                justifyContent: 'center', alignItems: 'center',
                                fontSize: '15px', padding: '14px',
                            }}
                        >
                            {loading ? '⏳ Registering Patient...' : '➕ Register Patient'}
                        </button>
                    </div>

                    {/* ===== Success / Error Card ===== */}
                    {registrationResult && !registrationResult.error && (
                        <div style={styles.glassCard}>
                            <h3 style={{ color: '#22c55e', marginBottom: '16px', fontSize: '16px' }}>✅ Patient Registered</h3>
                            <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '12px', padding: '24px', textAlign: 'center' as const, marginBottom: '18px' }}>
                                <div style={{ fontSize: '11px', color: 'rgba(148,163,184,0.5)', textTransform: 'uppercase' as const, letterSpacing: '0.1em' }}>VaidyaMitra Patient ID</div>
                                <div style={{ fontSize: '32px', fontWeight: 700, color: '#22d3ee', marginTop: '4px' }}>{registrationResult.patient_id}</div>
                            </div>
                            <div style={{ fontSize: '14px', color: 'rgba(203,213,225,0.8)', lineHeight: 2 }}>
                                <p><strong>Name:</strong> {registrationResult.name}</p>
                                <p><strong>Age / Gender:</strong> {registrationResult.age} yrs / {registrationResult.gender === 'M' ? 'Male' : registrationResult.gender === 'F' ? 'Female' : 'Other'}</p>
                                <p><strong>Blood Group:</strong> {registrationResult.blood_group}</p>
                                {registrationResult.phone && <p><strong>Phone:</strong> {registrationResult.phone}</p>}
                                {registrationResult.aadhaar_no && <p><strong>Aadhaar:</strong> ••••-••••-{registrationResult.aadhaar_no.slice(-4)}</p>}
                                {registrationResult.abha_no && <p><strong>ABHA:</strong> ••-••••-••••-{registrationResult.abha_no.slice(-4)}</p>}
                                {registrationResult.email && <p><strong>Email:</strong> {registrationResult.email}</p>}
                                {registrationResult.allergies?.length > 0 && (
                                    <div style={{ marginTop: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' as const }}>
                                        <span style={{ fontSize: '12px', color: 'rgba(148,163,184,0.5)' }}>Allergies:</span>
                                        {registrationResult.allergies.map((a: string, i: number) => (
                                            <span key={i} style={{ ...styles.chip, background: 'rgba(239,68,68,0.12)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.2)' }}>{a}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <button onClick={() => setRegistrationResult(null)} style={{ ...styles.btnSecondary, width: '100%', marginTop: '16px', textAlign: 'center' as const }}>
                                ➕ Register Another Patient
                            </button>
                        </div>
                    )}
                    {registrationResult?.error && (
                        <div style={{ ...styles.glassCard, border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.03)' }}>
                            <p style={{ color: '#ef4444', fontSize: '14px', margin: '0 0 12px' }}>❌ Registration failed</p>
                            <p style={{ color: 'rgba(203,213,225,0.6)', fontSize: '13px', margin: 0 }}>{registrationResult.error}</p>
                            <button onClick={() => setRegistrationResult(null)} style={{ ...styles.btnSecondary, marginTop: '12px' }}>Dismiss</button>
                        </div>
                    )}
                </div>
            )}

            {/* ========== SEARCH TAB ========== */}
            {activeTab === 'search' && (
                <div>
                    <div style={{ display: 'flex', gap: '12px', marginBottom: '22px' }}>
                        <input
                            id="search-input"
                            placeholder="Search by name, phone, Aadhaar, ABHA, or Patient ID..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSearch()}
                            style={{ ...fieldInput, flex: 1 }}
                        />
                        <button onClick={handleSearch} disabled={loading} style={{ ...styles.btnPrimary, whiteSpace: 'nowrap' as const, minWidth: '120px' }}>
                            {loading ? '⏳' : '🔍'} Search
                        </button>
                    </div>

                    {patients.length > 0 && (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '14px' }}>
                            {patients.map((p: any) => (
                                <div key={p.patient_id} onClick={() => fetchPatientDetails(p.patient_id)}
                                    style={{ ...styles.glassCard, cursor: 'pointer', transition: 'all 0.2s', borderLeft: '3px solid rgba(34,211,238,0.3)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                        <span style={{ color: '#22d3ee', fontWeight: 700, fontSize: '14px', fontFamily: 'monospace' }}>{p.patient_id}</span>
                                        <span style={{ ...styles.chip, fontSize: '11px' }}>{p.blood_group}</span>
                                    </div>
                                    <h4 style={{ color: '#fff', margin: '0 0 4px', fontSize: '15px' }}>{p.name}</h4>
                                    <p style={{ color: 'rgba(203,213,225,0.5)', fontSize: '13px', margin: 0 }}>
                                        {p.age} yrs · {p.gender === 'M' ? 'Male' : p.gender === 'F' ? 'Female' : 'Other'}
                                        {p.phone && ` · ${p.phone}`}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}

                    {patients.length === 0 && hasSearched && !loading && (
                        <div style={{ ...styles.glassCard, textAlign: 'center' as const, padding: '40px' }}>
                            <p style={{ color: 'rgba(203,213,225,0.5)', fontSize: '15px', margin: 0 }}>No patients found matching &quot;{searchQuery}&quot;</p>
                        </div>
                    )}

                    {selectedPatient && (
                        <div style={{ ...styles.glassCard, marginTop: '20px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                <h3 style={{ color: '#22d3ee', fontSize: '16px', margin: 0 }}>
                                    📋 Patient Details — {selectedPatient.patient?.patient_id || selectedPatient.patient_id}
                                </h3>
                                <button onClick={() => setSelectedPatient(null)} style={{ background: 'none', border: 'none', color: 'rgba(148,163,184,0.5)', cursor: 'pointer', fontSize: '18px' }}>✕</button>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', fontSize: '14px', color: 'rgba(203,213,225,0.8)' }}>
                                <div style={{ lineHeight: 2 }}>
                                    <p><strong>Name:</strong> {selectedPatient.patient?.name || selectedPatient.name}</p>
                                    <p><strong>Age:</strong> {selectedPatient.patient?.age || selectedPatient.age} yrs</p>
                                    <p><strong>Gender:</strong> {selectedPatient.patient?.gender === 'M' ? 'Male' : selectedPatient.patient?.gender === 'F' ? 'Female' : 'Other'}</p>
                                    <p><strong>Blood Group:</strong> {selectedPatient.patient?.blood_group || selectedPatient.blood_group}</p>
                                    <p><strong>Marital Status:</strong> {selectedPatient.patient?.marital_status || '—'}</p>
                                    <p><strong>Occupation:</strong> {selectedPatient.patient?.occupation || '—'}</p>
                                </div>
                                <div style={{ lineHeight: 2 }}>
                                    <p><strong>Phone:</strong> {selectedPatient.patient?.phone || '—'}</p>
                                    <p><strong>Email:</strong> {selectedPatient.patient?.email || '—'}</p>
                                    <p><strong>ABHA:</strong> {selectedPatient.patient?.abha_no ? `••-••••-••••-${selectedPatient.patient.abha_no.slice(-4)}` : '—'}</p>
                                    <p><strong>Address:</strong> {[selectedPatient.patient?.city, selectedPatient.patient?.state].filter(Boolean).join(', ') || '—'}</p>
                                    <p><strong>Total Visits:</strong> {selectedPatient.summary?.total_visits || 0}</p>
                                </div>
                            </div>
                            {(selectedPatient.patient?.allergies?.length > 0 || selectedPatient.allergies?.length > 0) && (
                                <div style={{ marginTop: '14px', display: 'flex', gap: '6px', flexWrap: 'wrap' as const, alignItems: 'center' }}>
                                    <span style={{ fontSize: '12px', color: 'rgba(148,163,184,0.5)' }}>Allergies:</span>
                                    {(selectedPatient.patient?.allergies || selectedPatient.allergies || []).map((a: string, i: number) => (
                                        <span key={i} style={{ ...styles.chip, background: 'rgba(239,68,68,0.12)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.2)' }}>{a}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </main>
    );
}
