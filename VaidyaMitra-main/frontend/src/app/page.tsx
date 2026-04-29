'use client';
import Link from 'next/link';
import { useRole } from '@/lib/RoleContext';

/* ================== SHARED MODULES ================== */
const systemModules = [
    { icon: '🔐', name: 'DataGuard Privacy', detail: 'MS Presidio · Aadhaar/PAN/PHI masking', dot: 'bg-red-500' },
    { icon: '🧠', name: 'Clinical Engine', detail: 'Summary · Change Detection · OCR', dot: 'bg-blue-500' },
    { icon: '🤖', name: 'Bedrock AI', detail: 'Meta Llama 3 · RAG grounded', dot: 'bg-indigo-500' },
    { icon: '🔬', name: 'Disease Predictor', detail: 'Medicure ML · 60+ conditions', dot: 'bg-amber-500' },
    { icon: '💊', name: 'Medicine Engine', detail: 'Jan Aushadhi KB · 50+ medicines', dot: 'bg-emerald-500' },
    { icon: '📄', name: 'Report Simplifier', detail: 'Jargon → Grade 6 readability', dot: 'bg-pink-500' },
    { icon: '🌐', name: 'Multilingual', detail: '9 Indian languages + English', dot: 'bg-cyan-500' },
];

/* ================== DOCTOR DATA ================== */
const docStats = [
    { label: 'Patients Registered', value: '1,247', icon: '👤', color: 'text-sky-600', bg: 'bg-sky-50 dark:bg-sky-500/10', border: 'border-sky-100 dark:border-sky-500/20', trend: '+12 today' },
    { label: 'Visits Recorded', value: '3,892', icon: '🏥', color: 'text-indigo-600', bg: 'bg-indigo-50 dark:bg-indigo-500/10', border: 'border-indigo-100 dark:border-indigo-500/20', trend: '+45 today' },
    { label: 'Reports Simplified', value: '856', icon: '📄', color: 'text-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-500/10', border: 'border-emerald-100 dark:border-emerald-500/20', trend: '+5 today' },
    { label: 'PII Entities Masked', value: '34,291', icon: '🔐', color: 'text-amber-600', bg: 'bg-amber-50 dark:bg-amber-500/10', border: 'border-amber-100 dark:border-amber-500/20', trend: '100% enforced' },
];

const docFeatures = [
    { icon: '👤', title: 'Patient Management', desc: 'Register, assign VM-IDs, track visits', href: '/patients', color: 'text-sky-500' },
    { icon: '📋', title: 'Clinical Data', desc: 'Comprehensive clinical intake with OCR auto-fill', href: '/clinical', color: 'text-blue-500' },
    { icon: '🔒', title: 'Medical Records', desc: 'Privacy-masked EHR-style records viewer', href: '/records', color: 'text-indigo-500' },
    { icon: '📄', title: 'Report Simplifier', desc: 'AI converts complex reports to easy language', href: '/reports', color: 'text-amber-500' },
    { icon: '🎤', title: 'Voice Query', desc: 'Speak in 9 Indian languages — AI responds', href: '/voice', color: 'text-orange-500' },
    { icon: '🤖', title: 'AI Query', desc: 'Agentic RAG-grounded clinical assistant', href: '/query', color: 'text-cyan-500' },
];

const docActivity = [
    { text: 'Patient VM-R4K92F registered with Aadhaar verification', dot: 'bg-sky-500', time: '1m' },
    { text: 'Lab report OCR extracted — 14 fields auto-filled', dot: 'bg-blue-500', time: '3m' },
    { text: 'Medical report simplified to Grade 6 readability', dot: 'bg-emerald-500', time: '5m' },
    { text: '8 PII entities masked via DataGuard before AI processing', dot: 'bg-amber-500', time: '9m' },
];

/* ================== PATIENT DATA ================== */
const patStats = [
    { label: 'Reports Simplified', value: '14', icon: '📄', color: 'text-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-500/10', border: 'border-emerald-100 dark:border-emerald-500/20', trend: 'Latest: CBC Test' },
    { label: 'Savings Generated', value: '₹4,250', icon: '💊', color: 'text-indigo-600', bg: 'bg-indigo-50 dark:bg-indigo-500/10', border: 'border-indigo-100 dark:border-indigo-500/20', trend: 'Jan Aushadhi' },
    { label: 'Queries Answered', value: '89', icon: '🤖', color: 'text-sky-600', bg: 'bg-sky-50 dark:bg-sky-500/10', border: 'border-sky-100 dark:border-sky-500/20', trend: '2 in Marathi' },
    { label: 'Health Score', value: 'Good', icon: '❤️', color: 'text-pink-600', bg: 'bg-pink-50 dark:bg-pink-500/10', border: 'border-pink-100 dark:border-pink-500/20', trend: 'Stable' },
];

const patFeatures = [
    { icon: '📄', title: 'Report Simplifier', desc: 'Convert complex lab reports to plain language', href: '/reports', color: 'text-emerald-500' },
    { icon: '🔬', title: 'Disease Prediction', desc: 'Symptom-based AI risk assessment', href: '/predict', color: 'text-pink-500' },
    { icon: '💊', title: 'Jan Aushadhi', desc: 'Find affordable generic medicine alternatives', href: '/medicine', color: 'text-indigo-500' },
    { icon: '🧪', title: 'Medicine Identifier', desc: 'Identify & compare branded vs generic', href: '/identify', color: 'text-blue-500' },
    { icon: '🤖', title: 'AI Assistant', desc: 'Ask any health question 24/7', href: '/query', color: 'text-cyan-500' },
    { icon: '🎤', title: 'Voice Query', desc: 'Ask questions in your regional language', href: '/voice', color: 'text-orange-500' },
];

const patActivity = [
    { text: 'Downloaded simplified explanation of Lipid Profile', dot: 'bg-emerald-500', time: '2 hrs ago' },
    { text: 'Found generic alternative: Augmentin → Amoxyclav (79% savings)', dot: 'bg-indigo-500', time: '1 day ago' },
    { text: 'Voice query processed in Hindi: "Diabetes ke lakshan kya hain?"', dot: 'bg-orange-500', time: '2 days ago' },
];


export default function Dashboard() {
    const { role } = useRole();
    const isDoctor = role === 'doctor';

    const stats = isDoctor ? docStats : patStats;
    const features = isDoctor ? docFeatures : patFeatures;
    const activity = isDoctor ? docActivity : patActivity;

    return (
        <main className="min-h-screen p-8 lg:p-12 transition-colors duration-200 bg-[var(--bg-main)]">
            {/* Header */}
            <div className="mb-10">
                <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--text-primary)] transition-colors">
                    {isDoctor ? 'Doctor Overview' : 'Patient Dashboard'}
                </h1>
                <p className="mt-2 text-base text-[var(--text-muted)] font-medium">
                    {isDoctor
                        ? 'Privacy-first clinical intelligence & practice management'
                        : 'Your personalized health insights & affordable medicine tools'
                    }
                </p>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                {stats.map((s, i) => (
                    <div key={i} className={`flex items-center gap-4 rounded-2xl border p-6 shadow-sm hover:shadow-md transition-all duration-200 bg-[var(--bg-glass)] border-[var(--border-glass)]`}>
                        <div className="text-3xl flex-shrink-0 drop-shadow-sm">{s.icon}</div>
                        <div className="flex-1 min-w-0">
                            <div className={`text-2xl font-bold tracking-tight leading-tight ${s.color}`}>{s.value}</div>
                            <div className="text-sm font-medium text-[var(--text-secondary)] mt-1">{s.label}</div>
                            <div className="text-xs font-semibold text-[var(--text-muted)] mt-1">{s.trend}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Feature Grid */}
            <div className="mb-10">
                <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mb-4 ml-1">Quick Access</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                    {features.map((f) => (
                        <Link key={f.href} href={f.href} className="group block outline-none">
                            <div className="flex items-center gap-4 p-5 rounded-2xl bg-[var(--bg-glass)] border border-[var(--border-glass)] shadow-[var(--shadow-card)] hover:shadow-md hover:border-[var(--accent-primary)] hover:-translate-y-0.5 transition-all duration-200">
                                <span className="text-2xl flex-shrink-0 group-hover:scale-110 transition-transform duration-200">{f.icon}</span>
                                <div className="min-w-0 flex-1">
                                    <div className="text-[15px] font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">{f.title}</div>
                                    <div className="text-sm text-[var(--text-muted)] truncate mt-0.5">{f.desc}</div>
                                </div>
                                <div className={`text-lg font-bold flex-shrink-0 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200 ${f.color}`}>
                                    →
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Bottom Section */}
            <div className={`grid grid-cols-1 ${isDoctor ? 'xl:grid-cols-2' : ''} gap-8`}>
                {/* Architecture (Only shown to doctor for technical detail) */}
                {isDoctor && (
                    <div className="p-6 md:p-8 rounded-2xl bg-[var(--bg-glass)] border border-[var(--border-glass)] shadow-[var(--shadow-card)]">
                        <h3 className="flex items-center gap-2 text-[15px] font-bold text-[var(--text-primary)] mb-6">
                            <span>⚙️</span> System Architecture
                        </h3>
                        <div className="space-y-1">
                            {systemModules.map((s, i) => (
                                <div key={i} className="flex items-center gap-4 py-3 border-b border-[var(--border-glass)] last:border-0 hover:bg-[var(--bg-card-hover)] px-2 -mx-2 rounded-lg transition-colors">
                                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${s.dot} shadow-sm`} />
                                    <span className="text-lg flex-shrink-0">{s.icon}</span>
                                    <div className="min-w-0 flex-1">
                                        <div className="text-[14px] font-semibold text-[var(--text-primary)]">{s.name}</div>
                                        <div className="text-xs text-[var(--text-muted)] mt-0.5">{s.detail}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Activity */}
                <div className="p-6 md:p-8 rounded-2xl bg-[var(--bg-glass)] border border-[var(--border-glass)] shadow-[var(--shadow-card)]">
                    <h3 className="flex items-center gap-2 text-[15px] font-bold text-[var(--text-primary)] mb-6">
                        <span>📊</span> Recent Activity
                    </h3>
                    <div className="space-y-1">
                        {activity.map((a, i) => (
                            <div key={i} className="flex items-start gap-4 py-3 border-b border-[var(--border-glass)] last:border-0 hover:bg-[var(--bg-card-hover)] px-2 -mx-2 rounded-lg transition-colors">
                                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-2 ${a.dot} shadow-sm`} />
                                <div className="flex-1 min-w-0">
                                    <div className="text-[14px] leading-relaxed text-[var(--text-secondary)]">{a.text}</div>
                                </div>
                                <span className="text-xs font-medium text-[var(--text-dimmed)] whitespace-nowrap pt-0.5">{a.time}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </main>
    );
}
