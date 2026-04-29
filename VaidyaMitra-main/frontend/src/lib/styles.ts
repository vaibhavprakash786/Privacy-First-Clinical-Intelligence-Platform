/**
 * Shared inline style objects for the VaidyaMitra healthcare theme.
 */

import type { CSSProperties } from 'react';

const glassCard: CSSProperties = {
    borderRadius: '16px',
    border: '1px solid var(--border-glass)',
    background: 'var(--bg-glass)',
    boxShadow: 'var(--shadow-card)',
    padding: '24px',
    transition: 'background 0.2s, border-color 0.2s, box-shadow 0.2s',
};

const inputField: CSSProperties = {
    width: '100%',
    padding: '12px 16px',
    borderRadius: '12px',
    color: 'var(--text-input)',
    background: 'var(--bg-input)',
    border: '1px solid var(--border-input)',
    outline: 'none',
    transition: 'all 0.2s',
    fontSize: '14px',
};

const btnPrimary: CSSProperties = {
    background: 'var(--accent-gradient)',
    boxShadow: 'var(--shadow-btn)',
    borderRadius: '12px',
    padding: '12px 24px',
    fontWeight: 600,
    color: '#ffffff',
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'inline-flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '8px',
};

const btnSecondary: CSSProperties = {
    background: 'var(--btn-inactive-bg)',
    border: '1px solid var(--border-input)',
    borderRadius: '12px',
    padding: '12px 24px',
    fontWeight: 600,
    color: 'var(--text-primary)',
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'inline-flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '8px',
};

const btnAccent: CSSProperties = {
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    boxShadow: '0 4px 14px 0 rgba(16, 185, 129, 0.39)',
    borderRadius: '12px',
    padding: '12px 24px',
    fontWeight: 600,
    color: '#ffffff',
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.2s',
};

const gradientText: CSSProperties = {
    backgroundImage: 'var(--accent-gradient)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
};

const panel: CSSProperties = {
    borderRadius: '16px',
    border: '1px solid var(--border-glass)',
    padding: '32px',
    background: 'var(--bg-glass)',
    boxShadow: 'var(--shadow-card)',
    transition: 'background 0.2s, border-color 0.2s',
};

const mainContent: CSSProperties = {
    minHeight: '100vh',
    padding: '32px 48px',
    background: 'var(--bg-main)',
    color: 'var(--text-primary)',
    transition: 'background 0.2s, color 0.2s',
};

const pageTitle: CSSProperties = {
    fontSize: '32px',
    fontWeight: 800,
    marginBottom: '8px',
    color: 'var(--text-primary)',
    letterSpacing: '-1px',
};

const pageSubtitle: CSSProperties = {
    color: 'var(--text-secondary)',
    fontSize: '15px',
    marginBottom: '32px',
    lineHeight: 1.5,
};

const chip: CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '4px 12px',
    borderRadius: '999px',
    fontSize: '12px',
    fontWeight: 600,
    background: 'var(--bg-chip)',
    color: 'var(--text-secondary)',
    border: '1px solid var(--border-chip)',
    whiteSpace: 'nowrap',
};

export const styles = {
    glassCard,
    inputField,
    btnPrimary,
    btnSecondary,
    btnAccent,
    gradientText,
    panel,
    mainContent,
    pageTitle,
    pageSubtitle,
    chip,
    input: inputField,
    buttonPrimary: btnPrimary,
};
