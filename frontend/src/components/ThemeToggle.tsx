import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="group relative flex h-10 w-10 items-center justify-center rounded-full border border-lazarus-border/70 bg-lazarus-surface/82 text-lazarus-text shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-lazarus-info/50 hover:text-lazarus-info hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lazarus-info/35 focus-visible:ring-offset-2 focus-visible:ring-offset-lazarus-bg"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      aria-pressed={isDark}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <span
        aria-hidden="true"
        className={`absolute inset-[3px] rounded-full border border-white/5 transition-all duration-200 ${
          isDark
            ? 'bg-lazarus-info/14 shadow-[0_0_18px_rgba(98,195,224,0.18)]'
            : 'bg-lazarus-surface-high/55'
        }`}
      />
      {isDark ? (
        <Sun className="relative h-4 w-4 transition-transform group-hover:rotate-45 group-hover:scale-110" />
      ) : (
        <Moon className="relative h-4 w-4 transition-transform group-hover:-rotate-12 group-hover:scale-110" />
      )}
    </button>
  )
}
