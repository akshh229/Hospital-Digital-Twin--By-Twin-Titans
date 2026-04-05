import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="group relative flex h-8 w-8 items-center justify-center rounded-full border border-lazarus-border/50 bg-white/60 dark:bg-lazarus-surface/60 text-lazarus-muted transition-all duration-200 hover:border-lazarus-info/40 hover:bg-lazarus-surface hover:text-lazarus-text hover:shadow-sm"
      aria-label="Toggle Theme"
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <Moon className="h-4 w-4 transition-transform group-hover:-rotate-12 group-hover:scale-110" />
      ) : (
        <Sun className="h-4 w-4 transition-transform group-hover:rotate-45 group-hover:scale-110" />
      )}
    </button>
  );
}
