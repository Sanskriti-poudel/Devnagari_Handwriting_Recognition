import { Monitor, Moon, Sun } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { useThemeStore } from '@/stores/theme.store'
import { cn } from '@/lib/utils'
import type { ThemePreference } from '@/types'

const OPTIONS: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
]

export function AppearanceSettings() {
  const { theme, setTheme } = useThemeStore()

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Choose how Devanagari OCR looks on your device</CardDescription>
        </div>
      </CardHeader>
      <div className="grid grid-cols-3 gap-3">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setTheme(opt.value)}
            className={cn(
              'flex flex-col items-center gap-2 rounded-xl border p-4 transition-all duration-200',
              theme === opt.value
                ? 'border-violet-500 bg-violet-50/60 shadow-glow dark:bg-violet-500/10'
                : 'border-slate-200 hover:border-violet-300 dark:border-white/10 dark:hover:border-violet-500/30'
            )}
          >
            <opt.icon className={cn('h-5 w-5', theme === opt.value ? 'text-violet-600 dark:text-violet-400' : 'text-slate-400')} />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">{opt.label}</span>
          </button>
        ))}
      </div>
    </Card>
  )
}
