import axios from 'axios'
import { useAuthStore } from '@/stores/auth.store'
import { useSettingsStore } from '@/stores/settings.store'

export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API !== 'false'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30_000,
})

api.interceptors.request.use((config) => {
  config.baseURL = useSettingsStore.getState().apiBaseUrl || config.baseURL
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error || error.response?.data?.message || error.message || 'Something went wrong.'
    return Promise.reject(new Error(message))
  }
)
