'use client';
import { useRole } from '@/lib/RoleContext';
import Sidebar from '@/components/Sidebar';
import { type ReactNode } from 'react';

export default function AppLayout({ children }: { children: ReactNode }) {
    const { role, setRole } = useRole();

    if (!role) {
        // Welcome Screen
        return (
            <main className="min-h-screen bg-[var(--bg-main)] flex flex-col items-center justify-center p-6 relative overflow-hidden transition-colors duration-300">
                {/* Decorative background elements */}
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-sky-500/10 dark:bg-sky-500/5 blur-[120px] rounded-full pointer-events-none" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] bg-indigo-500/10 dark:bg-indigo-500/5 blur-[100px] rounded-full pointer-events-none" />

                <div className="max-w-4xl w-full z-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
                    <div className="text-center mb-16">
                        <div className="inline-flex h-20 w-20 mb-6 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-500 to-blue-600 text-4xl text-white shadow-xl shadow-sky-500/30">
                            ⚕
                        </div>
                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-[var(--text-primary)] mb-4">
                            Welcome to <span className="bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-blue-600 drop-shadow-sm">VaidyaMitra</span>
                        </h1>
                        <p className="text-lg md:text-xl text-[var(--text-secondary)] font-medium max-w-2xl mx-auto leading-relaxed">
                            Privacy-first clinical intelligence and AI-powered healthcare platform. Please select your role to continue.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
                        {/* Doctor Card */}
                        <button
                            onClick={() => setRole('doctor')}
                            className="group text-left p-8 rounded-[2rem] bg-[var(--bg-glass)] border-2 border-[var(--border-glass)] hover:border-sky-500 hover:shadow-[0_8px_40px_-12px_rgba(14,165,233,0.3)] transition-all duration-300 hover:-translate-y-1 outline-none relative overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-gradient-to-br from-sky-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                            <div className="h-16 w-16 mb-6 rounded-2xl bg-sky-500/10 text-sky-500 flex items-center justify-center text-3xl group-hover:scale-110 group-hover:bg-sky-500 group-hover:text-white transition-all duration-300 shadow-sm relative z-10">
                                👨‍⚕️
                            </div>
                            <h2 className="text-2xl font-bold text-[var(--text-primary)] group-hover:text-sky-500 transition-colors mb-2 relative z-10">Doctor / Clinic</h2>
                            <p className="text-[var(--text-muted)] leading-relaxed font-medium relative z-10">Access patient management, clinical records, report simplification, and AI clinical assistant.</p>

                            <div className="mt-8 flex items-center text-sm font-bold text-sky-500 opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 relative z-10">
                                Enter Workspace <span className="ml-2">→</span>
                            </div>
                        </button>

                        {/* Patient Card */}
                        <button
                            onClick={() => setRole('patient')}
                            className="group text-left p-8 rounded-[2rem] bg-[var(--bg-glass)] border-2 border-[var(--border-glass)] hover:border-emerald-500 hover:shadow-[0_8px_40px_-12px_rgba(16,185,129,0.3)] transition-all duration-300 hover:-translate-y-1 outline-none relative overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                            <div className="h-16 w-16 mb-6 rounded-2xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center text-3xl group-hover:scale-110 group-hover:bg-emerald-500 group-hover:text-white transition-all duration-300 shadow-sm relative z-10">
                                🧑
                            </div>
                            <h2 className="text-2xl font-bold text-[var(--text-primary)] group-hover:text-emerald-500 transition-colors mb-2 relative z-10">Patient</h2>
                            <p className="text-[var(--text-muted)] leading-relaxed font-medium relative z-10">Access report simplification, disease prediction, generic medicine alternatives, and AI queries.</p>

                            <div className="mt-8 flex items-center text-sm font-bold text-emerald-500 opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 relative z-10">
                                Enter Dashboard <span className="ml-2">→</span>
                            </div>
                        </button>
                    </div>

                    <div className="mt-16 text-center text-[13px] font-medium text-[var(--text-dimmed)] flex items-center justify-center gap-2">
                        <span>🔐 100% Privacy-First</span>
                        <span className="w-1 h-1 rounded-full bg-[var(--text-dimmed)] opacity-30"></span>
                        <span>Built for Bharat 🇮🇳</span>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 ml-[280px]">
                {children}
            </main>
        </div>
    );
}
