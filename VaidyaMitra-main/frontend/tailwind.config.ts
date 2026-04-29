import type { Config } from "tailwindcss";

export default {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                brand: {
                    50: '#eef7ff',
                    100: '#d9edff',
                    200: '#bce0ff',
                    300: '#8ecdff',
                    400: '#59b0ff',
                    500: '#338bff',
                    600: '#1a6af5',
                    700: '#1454e1',
                    800: '#1744b6',
                    900: '#193d8f',
                    950: '#142757',
                },
                accent: {
                    50: '#effef4',
                    100: '#d9ffe7',
                    200: '#b5fdd0',
                    300: '#7af8ab',
                    400: '#38ea78',
                    500: '#0fd157',
                    600: '#06ad45',
                    700: '#098839',
                    800: '#0d6b31',
                    900: '#0d582b',
                    950: '#013215',
                },
                surface: {
                    50: '#f0f4ff',
                    100: '#e0e8ff',
                    200: '#c7d2fe',
                    800: '#1e1b4b',
                    900: '#0f0e2a',
                    950: '#080720',
                },
            },
            fontFamily: {
                sans: ['var(--font-outfit)', 'Inter', 'system-ui', 'sans-serif'],
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'mesh-gradient': 'linear-gradient(135deg, #0f0e2a 0%, #1a1947 25%, #142757 50%, #0f0e2a 100%)',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'fade-in': 'fadeIn 0.6s ease-out forwards',
                'slide-up': 'slideUp 0.5s ease-out forwards',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(20px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                glow: {
                    '0%': { boxShadow: '0 0 5px rgba(51, 139, 255, 0.2)' },
                    '100%': { boxShadow: '0 0 20px rgba(51, 139, 255, 0.4)' },
                },
            },
        },
    },
    plugins: [],
} satisfies Config;
