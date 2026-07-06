import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AppSettings } from '@/types'

interface SettingsState extends AppSettings {
  update: (patch: Partial<AppSettings>) => void
  updateNotifications: (patch: Partial<AppSettings['notifications']>) => void
  updatePrivacy: (patch: Partial<AppSettings['privacy']>) => void
  reset: () => void
}

const DEFAULTS: AppSettings = {
  apiBaseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  language: 'en',
  notifications: {
    email: true,
    push: false,
    ocrComplete: true,
    weeklySummary: false,
  },
  defaultModel: 'crnn',
  downloadFormat: 'txt',
  privacy: {
    storeHistory: true,
    shareAnalytics: false,
  },
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULTS,
      update: (patch) => set((state) => ({ ...state, ...patch })),
      updateNotifications: (patch) =>
        set((state) => ({ notifications: { ...state.notifications, ...patch } })),
      updatePrivacy: (patch) => set((state) => ({ privacy: { ...state.privacy, ...patch } })),
      reset: () => set(DEFAULTS),
    }),
    { name: 'devnagari-ocr-settings' }
  )
)
