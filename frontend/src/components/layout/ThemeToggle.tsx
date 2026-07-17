import { AnimatePresence, motion } from 'framer-motion'
import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '@/stores/theme.store'
import { cn } from '@/lib/utils'

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useThemeStore()
  const isDark = resolvedTheme === 'dark'

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label="Toggle dark mode"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      className={cn(
        'relative flex h-9 w-16 items-center rounded-full border border-slate-200 bg-slate-100 px-1 transition-colors duration-300 dark:border-white/10 dark:bg-white/[0.06]',
        className
      )}
    >
      <motion.span
        className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-brand shadow-glow"
        layout
        transition={{ type: 'spring', stiffness: 500, damping: 32 }}
        style={{ marginLeft: isDark ? 'auto' : 0 }}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={isDark ? 'moon' : 'sun'}
            initial={{ rotate: -90, opacity: 0, scale: 0.6 }}
            animate={{ rotate: 0, opacity: 1, scale: 1 }}
            exit={{ rotate: 90, opacity: 0, scale: 0.6 }}
            transition={{ duration: 0.25 }}
            className="flex items-center justify-center text-white"
          >
            {isDark ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
          </motion.span>
        </AnimatePresence>
      </motion.span>
    </button>
  )
}
