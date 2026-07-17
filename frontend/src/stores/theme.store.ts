import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ThemePreference } from '@/types'

interface ThemeState {
  theme: ThemePreference
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: ThemePreference) => void
}

function resolveTheme(theme: ThemePreference): 'light' | 'dark' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return theme
}

function applyTheme(resolved: 'light' | 'dark') {
  document.documentElement.classList.toggle('dark', resolved === 'dark')
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'system',
      resolvedTheme: resolveTheme('system'),
      setTheme: (theme) => {
        const resolvedTheme = resolveTheme(theme)
        applyTheme(resolvedTheme)
        set({ theme, resolvedTheme })
      },
    }),
    {
      name: 'devnagari-ocr-theme',
      onRehydrateStorage: () => (state) => {
        if (!state) return
        applyTheme(resolveTheme(state.theme))
        state.resolvedTheme = resolveTheme(state.theme)
      },
    }
  )
)

if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const { theme, setTheme } = useThemeStore.getState()
    if (theme === 'system') setTheme('system')
  })
}
