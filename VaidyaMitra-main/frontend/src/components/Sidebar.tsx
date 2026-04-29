'use client';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTheme } from '@/lib/ThemeProvider';
import { useRole } from '@/lib/RoleContext';

export default function Sidebar() {
    const pathname = usePathname();
    const { toggleTheme, isDark } = useTheme();
    const { role, setRole } = useRole();

    let navSections = [];

    if (role === 'doctor') {
        navSections = [
            {
                label: 'CLINICAL',
                items: [
                    { href: '/', label: 'Overview', icon: '📊' },
                    { href: '/patients', label: 'Patient Management', icon: '👤' },
                    { href: '/clinical', label: 'Clinical Data', icon: '📋' },
                    { href: '/records', label: 'Medical Records', icon: '🔒' },
                ],
            },
            {
                label: 'AI TOOLS',
                items: [
                    { href: '/reports', label: 'Report Simplifier', icon: '📄' },
                ],
            },
            {
                label: 'ASSISTANT',
                items: [
                    { href: '/query', label: 'AI Query', icon: '🤖' },
                    { href: '/voice', label: 'Voice Query', icon: '🎤' },
                ],
            },
        ];
    } else {
        navSections = [
            {
                label: 'PATIENT PORTAL',
                items: [
                    { href: '/', label: 'Dashboard', icon: '📊' },
                ],
            },
            {
                label: 'HEALTH TOOLS',
                items: [
                    { href: '/reports', label: 'Report Simplifier', icon: '📄' },
                    { href: '/predict', label: 'Disease Prediction', icon: '🔬' },
                    { href: '/medicine', label: 'Generic Medicine', icon: '💊' },
                    { href: '/identify', label: 'Medicine Identifier', icon: '🧪' },
                ],
            },
            {
                label: 'ASSISTANT',
                items: [
                    { href: '/query', label: 'AI Query', icon: '🤖' },
                    { href: '/voice', label: 'Voice Query', icon: '🎤' },
                ],
            },
        ];
    }

    return (
        <aside className="fixed left-0 top-0 z-50 flex h-screen w-[280px] flex-col overflow-y-auto bg-[var(--bg-sidebar)] border-r border-[var(--border-sidebar)] transition-colors duration-300">
            {/* Logo */}
            <div className="px-5 py-6 border-b border-[var(--border-sidebar)]">
                <Link href="/" className="flex items-center gap-3 outline-none group">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 text-xl text-white shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform duration-200">
                        ⚕
                    </div>
                    <div>
                        <div className="text-[19px] font-extrabold tracking-tight text-[var(--accent-primary)] leading-tight">VaidyaMitra</div>
                        <div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--text-muted)]">Clinical Intelligence</div>
                    </div>
                </Link>
            </div>

            {/* Navigation Sections */}
            <nav className="flex-1 flex flex-col gap-1 px-3 py-4 overflow-y-auto">
                {navSections.map((section) => (
                    <div key={section.label} className="mt-4 first:mt-1">
                        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
                            {section.label}
                        </div>
                        <div className="space-y-1">
                            {section.items.map((item) => {
                                const isActive = pathname === item.href;
                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 outline-none transition-all duration-200 ${isActive
                                            ? 'bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] font-semibold shadow-sm'
                                            : 'text-[var(--nav-inactive-text)] font-medium hover:bg-[var(--bg-card-hover)] hover:text-[var(--text-primary)]'
                                            }`}
                                    >
                                        {isActive && (
                                            <div className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-md bg-[var(--accent-primary)] shadow-[0_0_8px_var(--accent-primary)] opacity-80" />
                                        )}
                                        <span className={`text-[18px] w-6 text-center flex-shrink-0 transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`}>
                                            {item.icon}
                                        </span>
                                        <span className="text-[14px] leading-tight flex-1">{item.label}</span>
                                    </Link>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </nav>

            {/* Theme Toggle + Switch Role + Footer */}
            <div className="px-5 py-4 border-t border-[var(--border-sidebar)] bg-[var(--bg-sidebar)] flex flex-col gap-3">
                <button
                    onClick={() => setRole(null)}
                    className="flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-card-hover)] px-3.5 py-2.5 text-[13px] font-bold text-sky-500 transition-all duration-200 hover:border-sky-500 hover:bg-sky-500 hover:text-white outline-none shadow-sm"
                >
                    <span className="text-lg">🔄</span> Switch Role
                </button>

                <button
                    onClick={toggleTheme}
                    className="flex w-full items-center gap-3 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-card-hover)] px-3.5 py-2.5 text-[13px] font-medium text-[var(--text-secondary)] transition-all duration-200 hover:border-[var(--text-muted)] hover:text-[var(--text-primary)] outline-none"
                >
                    <span className={`flex h-7 w-7 items-center justify-center rounded-lg text-sm transition-all duration-500 shadow-sm ${isDark ? 'bg-gradient-to-br from-indigo-500 to-violet-500' : 'bg-gradient-to-br from-amber-400 to-orange-500'
                        }`}>
                        {isDark ? '🌙' : '☀️'}
                    </span>
                    <span className="flex-1 text-left">Dark Mode</span>

                    {/* Minimal Toggle Track */}
                    <div className={`relative h-5 w-9 rounded-full transition-colors duration-300 ${isDark ? 'bg-indigo-500' : 'bg-[var(--border-glass)]'
                        }`}>
                        <div className={`absolute top-[2px] h-4 w-4 rounded-full shadow-sm transition-all duration-300 ${isDark ? 'bg-white left-[18px]' : 'bg-white left-[2px]'
                            }`} />
                    </div>
                </button>

                <div className="mt-2 text-center text-[11px] font-medium text-[var(--text-muted)]">
                    <div>🔐 AI-Powered | Privacy-First</div>
                    <div className="mt-1 opacity-80">Made for Bharat 🇮🇳</div>
                </div>
            </div>
        </aside>
    );
}
