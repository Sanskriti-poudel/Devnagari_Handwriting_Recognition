import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

export const fetchModels = () => api.get('/models').then(r => r.data)

export const runOCR = (file, modelName) => {
  const form = new FormData()
  form.append('file', file)
  form.append('model_name', modelName)
  return api.post('/ocr', form).then(r => r.data)
}

export const fetchHistory = (limit = 10) =>
  api.get('/history', { params: { limit } }).then(r => r.data)

export const checkHealth = () => api.get('/health').then(r => r.data)
