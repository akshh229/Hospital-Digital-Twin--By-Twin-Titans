import { MoonStar, SunMedium } from 'lucide-react'
import { useTheme, type AppTheme } from '../theme/ThemeProvider'

const themeOptions: Array<{
  value: AppTheme
  label: string
  icon: typeof SunMedium
}> = [
  { value: 'clinical-light', label: 'Light', icon: SunMedium },
  { value: 'navy', label: 'Navy', icon: MoonStar },
]

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <div
      role="group"
      aria-label="Theme switcher"
      className="inline-flex items-center gap-1 rounded-full border border-lazarus-border bg-lazarus-surface/92 p-1 shadow-[0_12px_28px_rgba(43,58,79,0.08)]"
    >
      {themeOptions.map(({ value, label, icon: Icon }) => {
        const isActive = theme === value

        return (
          <button
            key={value}
            type="button"
            onClick={() => setTheme(value)}
            aria-pressed={isActive}
            aria-label={`Switch to ${label} theme`}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-all ${
              isActive
                ? 'bg-lazarus-accent text-white shadow-[0_10px_24px_rgba(43,58,79,0.14)]'
                : 'text-lazarus-muted hover:bg-lazarus-surface-high hover:text-lazarus-text'
            }`}
          >
            <Icon size={13} strokeWidth={2.2} />
            <span>{label}</span>
          </button>
        )
      })}
    </div>
  )
}
