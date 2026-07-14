import axios from 'axios'
import { useAuthStore } from '@/stores/auth.store'
import { useSettingsStore } from '@/stores/settings.store'

export const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API !== 'false'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  // CPU-only OCR inference (no GPU) can genuinely take minutes for a
  // multi-line image or multi-page PDF — a short timeout reads as
  // "Recognition failed" even though the backend is still working.
  timeout: 300_000,
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
  async (error) => {
    let data = error.response?.data
    // responseType: 'blob' requests also receive Blob error bodies — the
    // FastAPI HTTPException detail is inside, not in error.message.
    if (data instanceof Blob && data.type.includes('json')) {
      try {
        data = JSON.parse(await data.text())
      } catch {
        // leave data as-is; falls through to error.message below
      }
    }
    const message = data?.error || data?.detail || data?.message || error.message || 'Something went wrong.'
    return Promise.reject(new Error(message))
  }
)
