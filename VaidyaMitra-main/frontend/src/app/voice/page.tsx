'use client';
import { useState, useRef, type ReactNode } from 'react';
import { voiceQuery } from '@/lib/api';

const LANGUAGES = [
    { code: 'en-IN', label: 'English', native: 'English', flag: '🇬🇧' },
    { code: 'hi-IN', label: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
    { code: 'bn-IN', label: 'Bengali', native: 'বাংলা', flag: '🇮🇳' },
    { code: 'ta-IN', label: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
    { code: 'te-IN', label: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
    { code: 'mr-IN', label: 'Marathi', native: 'मराठी', flag: '🇮🇳' },
    { code: 'gu-IN', label: 'Gujarati', native: 'ગુજરાતી', flag: '🇮🇳' },
    { code: 'kn-IN', label: 'Kannada', native: 'ಕನ್ನಡ', flag: '🇮🇳' },
    { code: 'ml-IN', label: 'Malayalam', native: 'മലയാളം', flag: '🇮🇳' },
    { code: 'pa-IN', label: 'Punjabi', native: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
    { code: 'or-IN', label: 'Odia', native: 'ଓଡ଼ିଆ', flag: '🇮🇳' },
    { code: 'as-IN', label: 'Assamese', native: 'অসমীয়া', flag: '🇮🇳' },
];

/* ======= Shared Classes ======= */
const inputClasses = "w-full box-border px-4 py-3 rounded-xl text-[14px] font-medium text-[var(--text-input)] bg-[var(--bg-input)] border border-[var(--border-input)] outline-none transition-all duration-200 focus:border-[var(--accent-primary)] focus:ring-4 focus:ring-[var(--accent-primary)]/10 placeholder:text-[var(--text-dimmed)] placeholder:font-normal hover:border-[var(--text-muted)] shadow-sm";
const cardClasses = "rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass)] shadow-[var(--shadow-card)] p-6 md:p-8 transition-all duration-300";

const activeLangClass = "bg-[var(--accent-primary)] text-white shadow-md shadow-sky-500/30 font-bold border-transparent hover:bg-sky-400";
const inactiveLangClass = "bg-[var(--bg-card-hover)] text-[var(--text-secondary)] border-[var(--border-glass)] hover:border-sky-500/50 hover:bg-sky-500/5 hover:text-sky-600 dark:hover:text-sky-400 font-medium";

/* ======= Sub-components ======= */
function SectionHeader({ icon, title }: { icon: string; title: string }) {
    return (
        <div className="flex items-center gap-3 mb-5">
            <span className="text-xl flex-shrink-0">{icon}</span>
            <h3 className="text-[16px] font-bold text-[var(--accent-primary)] m-0 tracking-tight">{title}</h3>
        </div>
    );
}

/* ======= Main Component ======= */
export default function VoicePage() {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [language, setLanguage] = useState('en-IN');
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [patientId, setPatientId] = useState('');
    const [error, setError] = useState('');
    const [isPlaying, setIsPlaying] = useState(false);
    const recognitionRef = useRef<any>(null);

    const startListening = () => {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            setError('Speech recognition is not supported in this browser. Please use Chrome.');
            return;
        }
        const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = language;
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event: any) => {
            let finalTranscript = '';
            for (let i = 0; i < event.results.length; i++) {
                finalTranscript += event.results[i][0].transcript;
            }
            setTranscript(finalTranscript);
        };

        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);

        recognitionRef.current = recognition;
        recognition.start();
        setIsListening(true);
        setTranscript('');
        setResult(null);
        setError('');
    };

    const stopListening = () => {
        recognitionRef.current?.stop();
        setIsListening(false);
    };

    const handleSubmit = async () => {
        if (!transcript.trim()) return;
        setLoading(true); setError('');
        try {
            const langCode = language.split('-')[0];
            const res = await voiceQuery(transcript, langCode, patientId || undefined);
            setResult(res.data);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Voice processing failed');
        }
        setLoading(false);
    };

    const speakResponse = (text: string) => {
        if (!('speechSynthesis' in window)) return;

        if (isPlaying) {
            window.speechSynthesis.cancel();
            setIsPlaying(false);
            return;
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language;
        utterance.rate = 0.9;

        utterance.onend = () => setIsPlaying(false);
        utterance.onerror = () => setIsPlaying(false);

        window.speechSynthesis.speak(utterance);
        setIsPlaying(true);
    };

    const handlePatientIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value.toUpperCase().replace(/[^A-Z0-9\-]/g, '').slice(0, 12);
        setPatientId(val);
    };

    return (
        <main className="min-h-screen p-8 lg:p-12 transition-colors duration-200 bg-[var(--bg-main)]">
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[var(--text-primary)] mb-2">🎤 Voice Query Assistant</h1>
            <p className="text-base text-[var(--text-secondary)] font-medium mb-8">Speak in any Indian language — AI processes and responds · Powered by Web Speech API</p>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                {/* ===== LEFT: Input ===== */}
                <div className="flex flex-col gap-6">
                    {/* Language selector */}
                    <div className={cardClasses}>
                        <SectionHeader icon="🌐" title="Select Language" />
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {LANGUAGES.map(l => {
                                const isActive = language === l.code;
                                return (
                                    <button
                                        key={l.code}
                                        onClick={() => setLanguage(l.code)}
                                        className={`flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border transition-all duration-200 select-none ${isActive ? activeLangClass : inactiveLangClass}`}
                                    >
                                        <span className="text-lg">{l.flag}</span>
                                        <span className="text-[13px]">{l.native}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Patient ID */}
                    <div className={cardClasses}>
                        <label className="block text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-3">Patient Context (Optional)</label>
                        <input
                            id="voice-patient-id"
                            placeholder="Patient ID (e.g., VM-ABC123)"
                            value={patientId}
                            onChange={handlePatientIdChange}
                            maxLength={12}
                            className={inputClasses}
                        />
                    </div>

                    {/* Mic button */}
                    <div className={`${cardClasses} flex flex-col items-center justify-center py-12`}>
                        <button
                            onClick={isListening ? stopListening : startListening}
                            className={`w-28 h-28 rounded-full flex items-center justify-center text-5xl transition-all duration-300 outline-none
                                ${isListening
                                    ? 'bg-gradient-to-br from-red-500 to-red-700 text-white shadow-[0_0_40px_rgba(239,68,68,0.5)] animate-pulse hover:scale-105'
                                    : 'bg-gradient-to-br from-sky-400 to-blue-500 text-white shadow-[0_10px_30px_rgba(14,165,233,0.3)] hover:scale-110 hover:shadow-[0_15px_40px_rgba(14,165,233,0.4)]'
                                }`}
                        >
                            <span className={isListening ? 'animate-bounce' : ''}>{isListening ? '⏹' : '🎤'}</span>
                        </button>
                        <p className={`mt-6 text-[14px] font-bold transition-colors ${isListening ? 'text-red-500' : 'text-[var(--text-muted)]'}`}>
                            {isListening ? '🔴 Listening... Tap to stop' : 'Tap to start speaking'}
                        </p>
                    </div>

                    {/* Transcript */}
                    {transcript && (
                        <div className={`${cardClasses} animate-in fade-in slide-in-from-bottom-4 duration-300`}>
                            <SectionHeader icon="📝" title="Transcription" />
                            <div className="bg-[var(--bg-body)] rounded-xl p-5 border border-[var(--border-glass)] mb-6 shadow-sm min-h-[100px] flex items-center">
                                <p className="text-[16px] font-medium text-[var(--text-primary)] leading-relaxed m-0">{transcript}</p>
                            </div>

                            <button
                                id="btn-process-voice"
                                onClick={handleSubmit}
                                disabled={loading}
                                className={`w-full px-6 py-4 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold rounded-xl shadow-[0_4px_14px_0_rgba(14,165,233,0.39)] hover:shadow-[0_6px_20px_0_rgba(14,165,233,0.39)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-md transition-all duration-200 text-[16px] flex justify-center items-center gap-2 ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                            >
                                {loading ? '⏳ Processing...' : '✨ Analyze Query'}
                            </button>
                        </div>
                    )}

                    {error && (
                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 shadow-sm flex items-center gap-3 animate-in fade-in">
                            <span className="text-xl">❌</span>
                            <p className="text-[14px] font-bold text-red-600 dark:text-red-400 m-0">{error}</p>
                        </div>
                    )}
                </div>

                {/* ===== RIGHT: Response ===== */}
                <div className="flex flex-col gap-6">
                    {result ? (
                        <div className={`${cardClasses} xl:sticky xl:top-8 animate-in slide-in-from-right-8 duration-500 flex flex-col h-fit`}>
                            <div className="flex justify-between items-center mb-6 pb-5 border-b border-[var(--border-glass)]">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl bg-sky-500/10 p-2 rounded-xl border border-sky-500/20 shadow-sm flex-shrink-0">🤖</span>
                                    <h3 className="text-[18px] font-bold text-[var(--accent-primary)] m-0 tracking-tight">AI Response</h3>
                                </div>
                                <button
                                    onClick={() => speakResponse(result.result?.response || '')}
                                    className={`px-4 py-2 rounded-xl text-[13px] font-bold shadow-sm transition-all outline-none flex items-center gap-2
                                        ${isPlaying
                                            ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 hover:bg-red-500/20'
                                            : 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20 hover:bg-sky-500/20'
                                        }`}
                                >
                                    {isPlaying ? <><span className="animate-pulse">🛑</span> Stop</> : <><span>🔊</span> Listen</>}
                                </button>
                            </div>

                            {result.detected_language && (
                                <div className="mb-6 flex">
                                    <div className="px-4 py-1.5 rounded-lg text-[12px] font-bold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 shadow-sm flex items-center gap-2">
                                        <span className="opacity-80">🌐</span> Detected Language: {result.detected_language}
                                    </div>
                                </div>
                            )}

                            <div className="bg-[var(--bg-body)] rounded-xl p-6 border border-[var(--border-glass)] shadow-inner">
                                <p className="text-[15px] font-medium text-[var(--text-secondary)] leading-loose m-0 whitespace-pre-wrap">
                                    {result.result?.response ? result.result.response : JSON.stringify(result.result, null, 2)}
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className={`${cardClasses} flex flex-col items-center justify-center text-center py-20 bg-[var(--bg-body)] border-dashed border-2 opacity-70 hover:opacity-100`}>
                            <div className="w-24 h-24 mb-6 rounded-full bg-sky-500/10 border border-sky-500/20 flex items-center justify-center shadow-inner">
                                <span className="text-5xl opacity-80">🎤</span>
                            </div>
                            <h3 className="text-[18px] font-bold text-[var(--text-primary)] mb-2">Ready for your voice</h3>
                            <p className="text-[14px] font-medium text-[var(--text-muted)] max-w-[250px] leading-relaxed m-0">
                                Select a language, tap the microphone, and ask about clinical data, diseases, or medicine alternatives.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}
