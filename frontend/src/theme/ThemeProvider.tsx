import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from 'react'

export type AppTheme = 'clinical-light' | 'navy'

interface ThemeContextValue {
  theme: AppTheme
  setTheme: (theme: AppTheme) => void
}

const STORAGE_KEY = 'lazarus-theme'
const ThemeContext = createContext<ThemeContextValue | null>(null)

function applyTheme(theme: AppTheme) {
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme === 'navy' ? 'dark' : 'light'
}

function resolveInitialTheme(): AppTheme {
  if (typeof window === 'undefined') {
    return 'clinical-light'
  }

  const storedTheme = window.localStorage.getItem(STORAGE_KEY)
  if (storedTheme === 'clinical-light' || storedTheme === 'navy') {
    applyTheme(storedTheme)
    return storedTheme
  }

  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'navy'
    : 'clinical-light'
  applyTheme(systemTheme)
  return systemTheme
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<AppTheme>(resolveInitialTheme)

  useEffect(() => {
    applyTheme(theme)
    window.localStorage.setItem(STORAGE_KEY, theme)
  }, [theme])

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)

  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }

  return context
}
