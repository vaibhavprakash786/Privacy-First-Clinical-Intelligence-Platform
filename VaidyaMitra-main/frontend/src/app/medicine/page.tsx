'use client';
import { useState, type ReactNode } from 'react';
import { findGenericMedicine, findGenericMedicineImage } from '@/lib/api';

const POPULAR_MEDICINES = [
    'Augmentin 625mg', 'Crocin Advance', 'Dolo 650', 'Azithral 500', 'Pan 40',
    'Telma 40', 'Glycomet 500', 'Ecosprin 75', 'Amlodac 5', 'Atorva 10',
    'Combiflam', 'Allegra 120', 'Montair LC', 'Thyronorm 50', 'Shelcal 500',
    'Zifi 200', 'Cipla Omez 20', 'Benadryl Cough', 'Calpol 500', 'Becosules',
];

const CATEGORIES = [
    { label: '🫀 Cardiac', meds: ['Telma 40', 'Ecosprin 75', 'Amlodac 5', 'Atorva 10'] },
    { label: '💊 Diabetes', meds: ['Glycomet 500', 'Glimepiride 2mg'] },
    { label: '🤒 Pain / Fever', meds: ['Dolo 650', 'Combiflam', 'Crocin Advance'] },
    { label: '🦠 Antibiotics', meds: ['Augmentin 625mg', 'Azithral 500', 'Zifi 200'] },
];

interface Alternative { generic_name: string; composition: string; strength: string; jan_aushadhi_price: number; branded_price: number; savings_amount: number; savings_percentage: number; manufacturer: string; }

/* ======= Shared Classes ======= */
const inputClasses = "w-full box-border px-4 py-3 rounded-xl text-[14px] font-medium text-[var(--text-input)] bg-[var(--bg-input)] border border-[var(--border-input)] outline-none transition-all duration-200 focus:border-[var(--accent-primary)] focus:ring-4 focus:ring-[var(--accent-primary)]/10 placeholder:text-[var(--text-dimmed)] placeholder:font-normal hover:border-[var(--text-muted)] shadow-sm";
const cardClasses = "rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass)] shadow-[var(--shadow-card)] p-6 md:p-8 transition-all duration-300";

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
export default function MedicinePage() {
    const [search, setSearch] = useState('');
    const [quantity, setQuantity] = useState(10);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<Record<string, unknown> | null>(null);
    const [error, setError] = useState('');

    const handleSearch = async (query?: string) => {
        const q = query || search;
        if (!q.trim()) return;
        setSearch(q);
        setLoading(true); setError(''); setResult(null);
        try { const res = await findGenericMedicine(q, quantity); setResult(res); }
        catch (err: unknown) { setError(err instanceof Error ? err.message : 'Search failed'); }
        finally { setLoading(false); }
    };

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setSearch('Analyzing wrapper image...');
        setLoading(true); setError(''); setResult(null);
        try {
            const res = await findGenericMedicineImage(file);
            setResult(res);
            setSearch(res.data?.brand_name || 'Image Analyzed');
        }
        catch (err: unknown) { setError(err instanceof Error ? err.message : 'Image analysis failed'); setSearch(''); }
        finally { setLoading(false); }
        e.target.value = ''; // Reset file input
    };

    const handleQtyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value.replace(/\D/g, '').slice(0, 3);
        setQuantity(val ? parseInt(val) : 1);
    };

    const data = result?.data as Record<string, unknown> | undefined;
    const alternatives = (data?.alternatives || []) as Alternative[];
    const explanation = String(data?.ai_explanation || '');
    let safetyNote = String(data?.safety_note || '');
    let clinicalDetails: any = null;

    try {
        if (safetyNote.trim().startsWith('{')) {
            clinicalDetails = JSON.parse(safetyNote);
            safetyNote = '';
        }
    } catch (e) { /* ignore parse errors */ }

    const totalSavings = Number(data?.total_savings || 0);

    return (
        <main className="min-h-screen p-8 lg:p-12 transition-colors duration-200 bg-[var(--bg-main)]">
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--text-primary)] mb-2">💊 Jan Aushadhi — Generic Medicine</h1>
            <p className="text-base text-[var(--text-secondary)] font-medium mb-8">Find affordable generic alternatives · Save up to 90% on healthcare costs</p>

            <div className={`grid grid-cols-1 ${result ? 'xl:grid-cols-2' : ''} gap-8 transition-all duration-500`}>
                {/* ===== LEFT: Search ===== */}
                <div className="flex flex-col gap-6">
                    <div className={cardClasses}>
                        <SectionHeader icon="🔍" title="Search Branded Medicine" subtitle="Enter name to find Jan Aushadhi generic alternatives" />

                        <div className="flex flex-col sm:flex-row gap-3 mb-5">
                            <div className="relative flex-1">
                                <input
                                    id="medicine-search"
                                    placeholder="e.g., Augmentin 625mg..."
                                    value={search}
                                    onChange={e => setSearch(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleSearch()}
                                    className={`${inputClasses} pr-12`}
                                />
                                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                    <input type="file" id="jan-file-input" accept="image/*" className="hidden" onChange={handleImageUpload} />
                                    <button
                                        onClick={() => document.getElementById('jan-file-input')?.click()}
                                        disabled={loading}
                                        className="text-2xl hover:scale-110 active:scale-95 transition-transform outline-none"
                                        title="Upload Medicine Wrapper"
                                    >
                                        📷
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="flex flex-wrap sm:flex-nowrap gap-4 items-center mb-2 bg-[var(--bg-body)] p-3 rounded-xl border border-[var(--border-glass)]">
                            <div className="flex items-center gap-3">
                                <label className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-widest">Quantity:</label>
                                <input
                                    id="medicine-qty"
                                    type="text"
                                    inputMode="numeric"
                                    value={quantity}
                                    onChange={handleQtyChange}
                                    className={`${inputClasses} w-16 text-center !py-2 !px-2`}
                                />
                                <span className="text-[12px] font-medium text-[var(--text-muted)]">units/month</span>
                            </div>

                            <div className="flex-1 hidden sm:block" />

                            <button
                                id="btn-search-medicine"
                                onClick={() => handleSearch()}
                                disabled={loading || !search.trim()}
                                className={`w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold rounded-xl shadow-[0_4px_14px_0_rgba(14,165,233,0.39)] hover:shadow-[0_6px_20px_0_rgba(14,165,233,0.39)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-md transition-all duration-200 text-[15px] flex justify-center items-center gap-2 ${loading || !search.trim() ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {loading ? '⏳ Searching...' : '🔍 Analyze Medicine'}
                            </button>
                        </div>
                    </div>

                    {/* Popular & Categories */}
                    <div className={cardClasses}>
                        <SectionHeader icon="⭐" title="Popular Medicines" subtitle="Click to search" />
                        <div className="flex flex-wrap gap-2.5 mb-6">
                            {POPULAR_MEDICINES.map(m => (
                                <button key={m} onClick={() => handleSearch(m)} className="px-3.5 py-1.5 rounded-lg text-[12px] font-medium transition-colors bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border border-[var(--border-glass)] hover:bg-[var(--accent-primary)] hover:text-white hover:border-[var(--accent-primary)] outline-none shadow-sm">{m}</button>
                            ))}
                        </div>

                        <div className="space-y-4">
                            {CATEGORIES.map(cat => (
                                <div key={cat.label} className="bg-[var(--bg-body)] p-4 rounded-xl border border-[var(--border-glass)] shadow-sm">
                                    <div className="text-[13px] font-bold text-[var(--accent-primary)] mb-3 tracking-tight">{cat.label}</div>
                                    <div className="flex flex-wrap gap-2">
                                        {cat.meds.map(m => (
                                            <button key={m} onClick={() => handleSearch(m)} className="px-3 py-1.5 rounded-lg text-[12px] font-semibold bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border-glass)] hover:bg-sky-500 hover:text-white transition-colors outline-none shadow-sm">{m}</button>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
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
                        {/* Savings Header */}
                        {totalSavings > 0 && (
                            <div className="bg-[var(--bg-glass)] border-2 border-emerald-500/40 rounded-2xl p-6 shadow-sm relative overflow-hidden">
                                <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl" />
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center relative z-10">
                                    <div className="bg-[var(--bg-body)] rounded-xl py-3 border border-emerald-500/10">
                                        <div className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-muted)] mb-1">Per Strip</div>
                                        <div className="text-[26px] font-extrabold text-emerald-500">₹{totalSavings.toFixed(0)}</div>
                                    </div>
                                    <div className="bg-emerald-500/10 rounded-xl py-3 border border-emerald-500/30 transform sm:scale-105 shadow-sm">
                                        <div className="text-[10px] font-bold tracking-widest uppercase text-emerald-600 dark:text-emerald-400 mb-1">Monthly (×{quantity})</div>
                                        <div className="text-[28px] font-extrabold text-emerald-600 dark:text-emerald-400">₹{(totalSavings * quantity).toFixed(0)}</div>
                                    </div>
                                    <div className="bg-[var(--bg-body)] rounded-xl py-3 border border-emerald-500/10">
                                        <div className="text-[10px] font-bold tracking-widest uppercase text-[var(--text-muted)] mb-1">Yearly</div>
                                        <div className="text-[26px] font-extrabold text-emerald-500">₹{(totalSavings * quantity * 12).toFixed(0)}</div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Alternatives */}
                        <div className={cardClasses}>
                            <SectionHeader icon="💊" title="Generic Alternatives" subtitle={`${alternatives.length} found`} />
                            {alternatives.length > 0 ? (
                                <div className="flex flex-col gap-4">
                                    {alternatives.map((alt, i) => (
                                        <div key={i} className="p-5 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-body)] hover:border-[var(--accent-primary)] hover:shadow-md transition-all duration-300">
                                            <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                                                        <span className="text-[16px] font-bold text-[var(--text-primary)]">{alt.generic_name}</span>
                                                        {alt.manufacturer && alt.manufacturer !== "BPPI" && (
                                                            <span className="text-[10px] bg-sky-500/10 text-sky-600 dark:text-sky-400 px-2 py-0.5 rounded-md font-bold border border-sky-500/20 tracking-wide">
                                                                CODE: {alt.manufacturer}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="text-[13px] font-medium text-[var(--text-secondary)] leading-snug">{alt.composition}</div>
                                                    {alt.strength && (
                                                        <div className="text-[11px] font-medium text-[var(--text-muted)] mt-1">{alt.strength}</div>
                                                    )}
                                                </div>
                                                <div className="text-left md:text-right w-full md:w-auto mt-2 md:mt-0 pt-3 md:pt-0 border-t md:border-0 border-[var(--border-glass)] flex flex-row items-center md:items-end justify-between md:flex-col">
                                                    <div>
                                                        <div className="flex items-baseline gap-2 md:justify-end">
                                                            <span className="text-[20px] font-extrabold text-emerald-500">₹{alt.jan_aushadhi_price.toFixed(2)}</span>
                                                            <span className="text-[13px] font-medium text-[var(--text-muted)] line-through">₹{alt.branded_price.toFixed(2)}</span>
                                                        </div>
                                                        <div className="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-wider md:text-right mt-0.5">*AI Estimated Base Price</div>
                                                    </div>
                                                    <span className="inline-block md:mt-2 px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 shadow-sm">
                                                        Save {alt.savings_percentage}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-center py-8 text-[var(--text-muted)] font-medium">No Jan Aushadhi alternatives found</p>
                            )}
                        </div>

                        {/* Clinical Dashboard Grid */}
                        {clinicalDetails && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Uses */}
                                <div className="bg-sky-500/5 border border-sky-500/20 rounded-xl p-5 shadow-sm">
                                    <h4 className="flex items-center gap-2 text-[14px] font-bold text-sky-600 dark:text-sky-400 mb-3"><span className="text-lg">✅</span> Uses & Indications</h4>
                                    <ul className="pl-5 m-0 text-[13px] font-medium text-[var(--text-secondary)] space-y-1.5 list-disc marker:text-sky-400">
                                        {clinicalDetails.uses?.map((u: string, i: number) => <li key={i}>{u}</li>)}
                                    </ul>
                                </div>

                                {/* Side Effects */}
                                <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-5 shadow-sm">
                                    <h4 className="flex items-center gap-2 text-[14px] font-bold text-red-600 dark:text-red-400 mb-3"><span className="text-lg">⚠️</span> Common Side Effects</h4>
                                    <ul className="pl-5 m-0 text-[13px] font-medium text-[var(--text-secondary)] space-y-1.5 list-disc marker:text-red-400">
                                        {clinicalDetails.side_effects?.map((s: string, i: number) => <li key={i}>{s}</li>)}
                                    </ul>
                                </div>

                                {/* Precautions (Spans both columns) */}
                                <div className="md:col-span-2 bg-amber-500/5 border border-amber-500/20 rounded-xl p-5 shadow-sm">
                                    <h4 className="flex items-center gap-2 text-[14px] font-bold text-amber-600 dark:text-amber-500 mb-4"><span className="text-lg">🛡️</span> Safety Precautions</h4>

                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                        <div className="bg-[var(--bg-glass)] p-3 rounded-lg border border-amber-500/10">
                                            <div className="text-[10px] font-bold text-amber-500/70 uppercase tracking-widest mb-1">🤰 Pregnancy</div>
                                            <div className="text-[13px] font-medium text-[var(--text-primary)]">{clinicalDetails.precautions?.pregnancy || 'Consult Doctor'}</div>
                                        </div>
                                        <div className="bg-[var(--bg-glass)] p-3 rounded-lg border border-amber-500/10">
                                            <div className="text-[10px] font-bold text-amber-500/70 uppercase tracking-widest mb-1">🚗 Driving</div>
                                            <div className="text-[13px] font-medium text-[var(--text-primary)]">{clinicalDetails.precautions?.driving || 'Proceed with caution'}</div>
                                        </div>
                                        <div className="bg-[var(--bg-glass)] p-3 rounded-lg border border-amber-500/10">
                                            <div className="text-[10px] font-bold text-amber-500/70 uppercase tracking-widest mb-1">🍷 Alcohol</div>
                                            <div className="text-[13px] font-medium text-[var(--text-primary)]">{clinicalDetails.precautions?.alcohol || 'Check interactions'}</div>
                                        </div>
                                    </div>

                                    {clinicalDetails.dosage_guidelines && (
                                        <div className="mt-5 pt-4 border-t border-amber-500/10">
                                            <div className="text-[10px] font-bold text-amber-500/80 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                                                <span>⏱️</span> Dosage Guidelines
                                            </div>
                                            <div className="text-[13px] font-medium text-[var(--text-primary)] bg-[var(--bg-glass)] px-3 py-2 rounded-lg border border-[var(--border-glass)] border-l-2 border-l-amber-500">{clinicalDetails.dosage_guidelines}</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Bioequivalence Comparison */}
                        {explanation && (
                            <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-6 shadow-sm">
                                <SectionHeader icon="⚖️" title="Bioequivalence & Price Analysis" />
                                <p className="text-[14px] font-medium text-[var(--text-secondary)] leading-loose m-0">{explanation}</p>
                            </div>
                        )}

                        {/* Fallback Safety Note (For unparsed strings) */}
                        {safetyNote && (
                            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-3 mt-1">
                                <span className="text-lg opacity-80 mt-0.5">⚠️</span>
                                <p className="text-[13px] font-bold text-amber-600 dark:text-amber-500 leading-relaxed m-0">{safetyNote}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </main>
    );
}
