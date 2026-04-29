'use client';
import { useState, type ReactNode } from 'react';
import { identifyMedicine, compareMedicine, listMedicines, identifyMedicineImage } from '@/lib/api';

/* ======= Shared Classes ======= */
const inputClasses = "w-full box-border px-5 py-3.5 rounded-xl text-[15px] font-medium text-[var(--text-input)] bg-[var(--bg-input)] border border-[var(--border-input)] outline-none transition-all duration-200 focus:border-[var(--accent-primary)] focus:ring-4 focus:ring-[var(--accent-primary)]/10 placeholder:text-[var(--text-dimmed)] placeholder:font-normal hover:border-[var(--text-muted)] shadow-sm";
const cardClasses = "rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass)] shadow-[var(--shadow-card)] p-6 md:p-8 transition-all duration-300";

function getScheduleColor(scheduleClass: string = '') {
    const sc = (scheduleClass || '').toLowerCase();
    if (sc.includes('otc')) return { bg: 'bg-emerald-500/10', color: 'text-emerald-600 dark:text-emerald-400', border: 'border-emerald-500/20' };
    if (sc.includes('h1') || sc.includes('x')) return { bg: 'bg-red-500/10', color: 'text-red-500', border: 'border-red-500/20' };
    if (sc.includes('h')) return { bg: 'bg-orange-500/10', color: 'text-orange-500 dark:text-orange-400', border: 'border-orange-500/20' };
    if (sc.includes('g')) return { bg: 'bg-purple-500/10', color: 'text-purple-500 dark:text-purple-400', border: 'border-purple-500/20' };
    return { bg: 'bg-[var(--bg-body)]', color: 'text-[var(--text-secondary)]', border: 'border-[var(--border-glass)]' };
}

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

function InfoRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex flex-col sm:flex-row gap-1 sm:gap-4 py-2.5 border-b border-[var(--border-glass)] last:border-0">
            <span className="text-[12px] uppercase tracking-widest font-bold text-[var(--text-muted)] sm:min-w-[120px] sm:pt-0.5">{label}</span>
            <span className="text-[14px] font-medium text-[var(--text-primary)] leading-snug">{value}</span>
        </div>
    );
}

function ChipList({ items, colorClasses }: { items: string[]; colorClasses: string }) {
    return (
        <div className="flex flex-wrap gap-2.5">
            {items.map((item, i) => (
                <span key={i} className={`px-3 py-1.5 rounded-lg text-[13px] font-semibold border shadow-sm ${colorClasses}`}>
                    {item}
                </span>
            ))}
        </div>
    );
}

/* ======= Main Component ======= */
export default function IdentifyPage() {
    const [query, setQuery] = useState('');
    const [result, setResult] = useState<any>(null);
    const [comparison, setComparison] = useState<any>(null);
    const [allMeds, setAllMeds] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [showAll, setShowAll] = useState(false);
    const [error, setError] = useState('');

    const handleIdentify = async () => {
        if (!query.trim()) return;
        setLoading(true); setError('');
        try {
            const [idRes, cmpRes] = await Promise.all([identifyMedicine(query), compareMedicine(query)]);
            setResult(idRes.data);
            setComparison(cmpRes.data);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed to identify');
        }
        setLoading(false);
    };

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setLoading(true); setError(''); setQuery(file.name);
        try {
            const idRes = await identifyMedicineImage(file);
            setResult(idRes.data);
            if (idRes.data?.identified && idRes.data.medicine?.brand) {
                const cmpRes = await compareMedicine(idRes.data.medicine.brand);
                setComparison(cmpRes.data);
            } else {
                setComparison(null);
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Failed to process image');
        }
        setLoading(false);
    };

    const handleShowAll = async () => {
        if (allMeds.length > 0) { setShowAll(!showAll); return; }
        try {
            const res = await listMedicines();
            setAllMeds(res.data || []);
            setShowAll(true);
        } catch { }
    };

    const med = result?.medicine;

    return (
        <main className="min-h-screen p-8 lg:p-12 transition-colors duration-200 bg-[var(--bg-main)]">
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--text-primary)] mb-2">🧪 Medicine Identifier</h1>
            <p className="text-base text-[var(--text-secondary)] font-medium mb-8">Identify any medicine — get full details, Jan Aushadhi comparison, and savings</p>

            {/* Search */}
            <div className={`${cardClasses} mb-6`}>
                <SectionHeader icon="🔍" title="Search Medicine" subtitle="Enter brand or generic name" />

                <div className="flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <input
                            id="medicine-identify-search"
                            placeholder="e.g., Dolo 650, Metformin, Augmentin..."
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleIdentify()}
                            className={inputClasses}
                        />
                    </div>

                    <div className="flex gap-3">
                        <button
                            id="btn-identify"
                            onClick={handleIdentify}
                            disabled={loading || !query.trim()}
                            className={`flex-1 md:flex-none px-8 py-3.5 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold rounded-xl shadow-[0_4px_14px_0_rgba(14,165,233,0.39)] hover:shadow-[0_6px_20px_0_rgba(14,165,233,0.39)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-md transition-all duration-200 text-[15px] whitespace-nowrap flex justify-center items-center ${loading || !query.trim() ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {loading ? '⏳ Analyzing...' : '🔍 Identify'}
                        </button>

                        <button
                            onClick={handleShowAll}
                            className={`flex-none px-6 py-3.5 rounded-xl text-[15px] font-bold border transition-all duration-200 whitespace-nowrap outline-none
                                ${showAll
                                    ? 'bg-[var(--accent-primary)] text-white border-transparent shadow-sm'
                                    : 'bg-[var(--bg-input)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] border-[var(--border-input)] shadow-sm'
                                }`}
                        >
                            📋 {showAll ? 'Hide DB' : 'View DB'}
                        </button>
                    </div>
                </div>

                <div className="flex items-center gap-4 my-6 opacity-60">
                    <div className="flex-1 h-px bg-[var(--border-glass)]"></div>
                    <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-widest">OR</span>
                    <div className="flex-1 h-px bg-[var(--border-glass)]"></div>
                </div>

                <div className="flex justify-center">
                    <label className="flex items-center gap-3 px-8 py-4 bg-sky-500/5 hover:bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-dashed border-sky-500/30 hover:border-sky-500/50 rounded-xl cursor-pointer text-[15px] font-bold transition-all duration-200 shadow-sm group">
                        <span className="text-xl group-hover:scale-110 transition-transform">📷</span> Upload Wrapper Image
                        <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" disabled={loading} />
                    </label>
                </div>
            </div>

            {error && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 shadow-sm flex items-center gap-3 animate-in fade-in mb-6">
                    <span className="text-xl">❌</span>
                    <p className="text-[14px] font-bold text-red-600 dark:text-red-400 m-0">{error}</p>
                </div>
            )}

            {/* All medicines list */}
            {showAll && allMeds.length > 0 && (
                <div className={`${cardClasses} mb-6 max-h-[400px] overflow-hidden flex flex-col animate-in slide-in-from-top-4 fade-in duration-300 p-0`}>
                    <div className="p-6 md:p-8 pb-4 border-b border-[var(--border-glass)] bg-[var(--bg-glass)] z-10 sticky top-0">
                        <SectionHeader icon="📋" title="All Medicines Database" subtitle={`${allMeds.length} medicines available`} />
                    </div>

                    <div className="overflow-auto flex-1 p-6 pt-0">
                        <table className="w-full text-left border-collapse min-w-[700px]">
                            <thead className="sticky top-0 bg-[var(--bg-glass)] backdrop-blur-md z-10">
                                <tr>
                                    {['Brand', 'Generic', 'Category', 'Branded ₹', 'Jan Aushadhi ₹', 'Savings %'].map((h, i) => (
                                        <th key={h} className={`px-4 py-3 text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider border-b border-[var(--border-glass)] ${i >= 3 ? 'text-right' : 'text-left'}`}>
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[var(--border-glass)]">
                                {allMeds.map((m: any, i: number) => (
                                    <tr key={i}
                                        onClick={() => { setQuery(m.brand); setShowAll(false); handleIdentify(); }}
                                        className="hover:bg-[var(--bg-body)] cursor-pointer transition-colors group">
                                        <td className="px-4 py-3.5 text-[14px] font-bold text-[var(--accent-primary)] group-hover:text-sky-500 transition-colors">{m.brand}</td>
                                        <td className="px-4 py-3.5 text-[13px] font-medium text-[var(--text-secondary)]">{m.generic}</td>
                                        <td className="px-4 py-3.5"><span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-[var(--bg-input)] border border-[var(--border-glass)] text-[var(--text-muted)]">{m.category}</span></td>
                                        <td className="px-4 py-3.5 text-[14px] font-medium text-[var(--text-secondary)] text-right">₹{m.branded_price}</td>
                                        <td className="px-4 py-3.5 text-[14px] font-bold text-emerald-500 text-right">₹{m.jan_aushadhi_price}</td>
                                        <td className="px-4 py-3.5 text-right">
                                            <span className="px-2 py-1 rounded-md text-[11px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                                                {m.savings_percentage}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Result */}
            {med && (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 animate-in slide-in-from-bottom-8 fade-in flex-1">
                    {/* Left: Medicine Info */}
                    <div className="flex flex-col gap-6">
                        <div className={cardClasses}>
                            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 mb-6">
                                <h3 className="text-[22px] font-extrabold text-[var(--text-primary)] m-0 tracking-tight">{med.brand}</h3>

                                <div className="flex flex-wrap gap-2">
                                    <span className="px-3 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wide bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 shadow-sm">
                                        {med.category}
                                    </span>

                                    {med.schedule_class && (() => {
                                        const scStyles = getScheduleColor(med.schedule_class);
                                        return (
                                            <span className={`px-3 py-1 rounded-lg text-[11px] font-extrabold uppercase tracking-widest ${scStyles.bg} ${scStyles.color} border ${scStyles.border} shadow-sm`}>
                                                {med.schedule_class}
                                            </span>
                                        );
                                    })()}
                                </div>
                            </div>

                            <div className="flex flex-col">
                                <InfoRow label="Generic Name" value={med.generic} />
                                <InfoRow label="Composition" value={med.composition} />
                                <InfoRow label="Usage" value={med.usage} />
                                <InfoRow label="Dosage" value={med.dosage} />
                                <InfoRow label="Strengths" value={med.available_strengths?.join(', ') || '—'} />
                            </div>
                        </div>

                        {/* Side Effects */}
                        {med.side_effects?.length > 0 && (
                            <div className={`${cardClasses} p-5 md:p-6`}>
                                <SectionHeader icon="⚠️" title="Side Effects" />
                                <ChipList items={med.side_effects} colorClasses="bg-amber-500/10 text-amber-600 dark:text-amber-500 border-amber-500/20" />
                            </div>
                        )}

                        {/* Variants */}
                        {med.variants?.length > 0 && (
                            <div className={`${cardClasses} p-5 md:p-6`}>
                                <SectionHeader icon="💊" title="Available Variants" />
                                <ChipList items={med.variants} colorClasses="bg-[var(--bg-input)] text-[var(--text-secondary)] border-[var(--border-glass)]" />
                            </div>
                        )}

                        {/* Similar Medicines */}
                        {med.similar_medicines?.length > 0 && (
                            <div className={`${cardClasses} p-5 md:p-6`}>
                                <SectionHeader icon="🔄" title="Similar Alternatives" subtitle="Other known brands" />
                                <ChipList items={med.similar_medicines} colorClasses="bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20" />
                            </div>
                        )}

                        {/* Interactions */}
                        {med.interactions?.length > 0 && (
                            <div className={`${cardClasses} p-5 md:p-6`}>
                                <SectionHeader icon="🚫" title="Drug Interactions" />
                                <ChipList items={med.interactions} colorClasses="bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20" />
                            </div>
                        )}
                    </div>

                    {/* Right: Detailed Clinical Info */}
                    <div className="flex flex-col gap-6">
                        <div className={cardClasses}>
                            <SectionHeader icon="⏱️" title="When to Take" />
                            <div className="p-4 rounded-xl bg-[var(--bg-body)] border border-[var(--border-glass)] text-[var(--text-primary)] font-medium text-[14px] leading-relaxed shadow-sm">
                                {med.when_to_take || "Consult your physician for specific timing instructions."}
                            </div>
                        </div>

                        {med.contraindications?.length > 0 && (
                            <div className={cardClasses}>
                                <SectionHeader icon="🛑" title="Do NOT Take If (Contraindications)" />
                                <div className="flex flex-col gap-2.5">
                                    {med.contraindications.map((ci: string, i: number) => (
                                        <div key={i} className="flex gap-3 p-3.5 rounded-xl bg-red-500/5 border border-red-500/20 text-red-600 dark:text-red-400 font-medium text-[13px] shadow-sm">
                                            <span className="flex-shrink-0 opacity-80 mt-0.5">•</span>
                                            <span>{ci}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {med.detailed_info && (
                            <div className={cardClasses}>
                                <SectionHeader icon="ℹ️" title="Detailed Information & Warnings" />
                                <div className="p-5 rounded-xl bg-[var(--bg-body)] border border-[var(--border-glass)] shadow-sm">
                                    <p className="m-0 text-[13px] font-medium leading-loose text-[var(--text-secondary)] whitespace-pre-line">
                                        {med.detailed_info}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Safety Note */}
                        <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 flex gap-3 shadow-sm mt-auto">
                            <span className="text-xl opacity-90 mt-0.5">🛡️</span>
                            <p className="text-[13px] font-medium text-emerald-600 dark:text-emerald-500/90 leading-relaxed m-0">
                                <strong className="font-extrabold text-emerald-600 dark:text-emerald-400">Always consult your doctor</strong> before starting, modifying, or stopping any medication. AI-generated insights are for reference only.
                            </p>
                        </div>
                    </div>

                    {/* Generic Equivalent Section (Full Width) */}
                    {med && med.generic_equivalent && (
                        <div className="xl:col-span-2">
                            <div className={`${cardClasses} bg-gradient-to-r from-emerald-500/5 to-[var(--bg-glass)] border-emerald-500/20 relative overflow-hidden`}>
                                <div className="absolute right-0 top-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>

                                <div className="flex items-center gap-4 mb-6 relative z-10">
                                    <div className="w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-500 flex items-center justify-center text-2xl shadow-sm border border-emerald-500/30 flex-shrink-0">
                                        🌿
                                    </div>
                                    <div>
                                        <h3 className="text-emerald-600 dark:text-emerald-400 text-[20px] font-extrabold m-0 tracking-tight">
                                            {med.generic_equivalent.name}
                                        </h3>
                                        <div className="text-[11px] font-bold text-emerald-500/80 uppercase tracking-widest mt-1">
                                            Cost-Effective Generic Alternative
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
                                    <div className="bg-[var(--bg-glass)] p-4 rounded-xl border border-emerald-500/10 shadow-sm backdrop-blur-sm">
                                        <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1.5">Composition</div>
                                        <div className="text-[14px] font-medium text-[var(--text-primary)] leading-snug">{med.generic_equivalent.composition}</div>
                                    </div>
                                    <div className="bg-[var(--bg-glass)] p-4 rounded-xl border border-emerald-500/10 shadow-sm backdrop-blur-sm">
                                        <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1.5">Typical Dosage</div>
                                        <div className="text-[14px] font-medium text-[var(--text-primary)] leading-snug">{med.generic_equivalent.dosage}</div>
                                    </div>
                                    <div className="md:col-span-2 bg-[var(--bg-glass)] p-4 rounded-xl border border-emerald-500/10 shadow-sm backdrop-blur-sm mt-1">
                                        <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1.5">Primary Usage</div>
                                        <div className="text-[14px] font-medium text-[var(--text-primary)] leading-relaxed">{med.generic_equivalent.usage}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {result && !result.identified && (
                <div className={`${cardClasses} text-center py-20 flex flex-col items-center justify-center border-dashed border-2 animate-in fade-in`}>
                    <div className="w-20 h-20 bg-[var(--bg-body)] rounded-full flex items-center justify-center text-4xl mb-5 shadow-inner border border-[var(--border-glass)]">
                        🔍
                    </div>
                    <p className="text-[15px] font-medium text-[var(--text-muted)] max-w-sm m-0 leading-relaxed">{result.suggestion}</p>
                </div>
            )}
        </main>
    );
}
