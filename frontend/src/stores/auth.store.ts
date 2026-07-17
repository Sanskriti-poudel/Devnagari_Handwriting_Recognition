import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authService } from '@/services/auth.service'
import type { AuthCredentials, SignupPayload, User } from '@/types'

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (credentials: AuthCredentials) => Promise<void>
  signup: (payload: SignupPayload) => Promise<void>
  logout: () => Promise<void>
  updateUser: (user: User) => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null })
        try {
          const { user, accessToken } = await authService.login(credentials)
          set({ user, accessToken, isAuthenticated: true, isLoading: false })
        } catch (err) {
          set({ isLoading: false, error: (err as Error).message })
          throw err
        }
      },

      signup: async (payload) => {
        set({ isLoading: true, error: null })
        try {
          const { user, accessToken } = await authService.signup(payload)
          set({ user, accessToken, isAuthenticated: true, isLoading: false })
        } catch (err) {
          set({ isLoading: false, error: (err as Error).message })
          throw err
        }
      },

      logout: async () => {
        await authService.logout()
        set({ user: null, accessToken: null, isAuthenticated: false })
      },

      updateUser: (user) => set({ user }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'devnagari-ocr-auth',
      partialize: (state) => ({ user: state.user, accessToken: state.accessToken, isAuthenticated: state.isAuthenticated }),
    }
  )
)
