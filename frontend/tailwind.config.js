/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'lazarus-bg': 'rgb(var(--color-lazarus-bg) / <alpha-value>)',
        'lazarus-surface-low': 'rgb(var(--color-lazarus-surface-low) / <alpha-value>)',
        'lazarus-surface': 'rgb(var(--color-lazarus-surface) / <alpha-value>)',
        'lazarus-surface-high': 'rgb(var(--color-lazarus-surface-high) / <alpha-value>)',
        'lazarus-border': 'rgb(var(--color-lazarus-border) / <alpha-value>)',
        'lazarus-text': 'rgb(var(--color-lazarus-text) / <alpha-value>)',
        'lazarus-muted': 'rgb(var(--color-lazarus-muted) / <alpha-value>)',
        'lazarus-critical': 'rgb(var(--color-lazarus-critical) / <alpha-value>)',
        'lazarus-warning': 'rgb(var(--color-lazarus-warning) / <alpha-value>)',
        'lazarus-normal': 'rgb(var(--color-lazarus-normal) / <alpha-value>)',
        'lazarus-info': 'rgb(var(--color-lazarus-info) / <alpha-value>)',
        'lazarus-accent': 'rgb(var(--color-lazarus-accent) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        display: ['Cormorant Garamond', 'Georgia', 'serif'],
        mono: ['IBM Plex Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-critical': '0 0 15px rgba(239, 68, 68, 0.3)',
      }
    },
  },
  plugins: [],
}
