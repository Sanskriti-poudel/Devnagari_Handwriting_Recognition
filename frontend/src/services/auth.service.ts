import { api, USE_MOCK_API } from '@/services/api'
import { mockDb } from '@/services/mock/mockDb'
import { sleep } from '@/lib/utils'
import type { AuthCredentials, SignupPayload, User } from '@/types'

export interface AuthResponse {
  user: User
  accessToken: string
}

export const authService = {
  async login({ email, password }: AuthCredentials): Promise<AuthResponse> {
    if (USE_MOCK_API) {
      await sleep(700)
      const user = mockDb.findUserByEmail(email)
      if (!user || user.password !== password) {
        throw new Error('Invalid email or password.')
      }
      mockDb.setSession(user.id)
      const { password: _p, ...rest } = user
      void _p
      return { user: rest, accessToken: `mock-token-${user.id}` }
    }
    const { data } = await api.post<AuthResponse>('/login', { email, password })
    return data
  },

  async signup({ fullName, email, password }: SignupPayload): Promise<AuthResponse> {
    if (USE_MOCK_API) {
      await sleep(900)
      const user = mockDb.createUser(fullName, email, password)
      mockDb.setSession(user.id)
      return { user, accessToken: `mock-token-${user.id}` }
    }
    const { data } = await api.post<AuthResponse>('/signup', { fullName, email, password })
    return data
  },

  async logout(): Promise<void> {
    if (USE_MOCK_API) {
      await sleep(200)
      mockDb.setSession(null)
      return
    }
    await api.post('/logout')
  },

  async refreshToken(): Promise<AuthResponse | null> {
    if (USE_MOCK_API) {
      const user = mockDb.getSessionUser()
      if (!user) return null
      return { user, accessToken: `mock-token-${user.id}` }
    }
    const { data } = await api.post<AuthResponse>('/refresh-token')
    return data
  },

  async forgotPassword(email: string): Promise<void> {
    if (USE_MOCK_API) {
      await sleep(800)
      return
    }
    await api.post('/forgot-password', { email })
  },

  async resetPassword(token: string, password: string): Promise<void> {
    if (USE_MOCK_API) {
      await sleep(800)
      return
    }
    await api.post('/reset-password', { token, password })
  },
}
