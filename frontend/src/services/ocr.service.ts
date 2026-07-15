import { api } from '@/services/api'
import { mockDb } from '@/services/mock/mockDb'
import type { OcrModelId, OcrResult } from '@/types'

function uid(prefix = 'id') {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 6)}`
}

function fileToDataUri(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

interface DocumentApiResponse {
  text: string
  num_chars: number
  num_lines: number
  avg_confidence: number
  time_ms: number
  annotated?: string
  model_simulated: boolean
}

export const ocrService = {
  /**
   * Runs the real, trained backend (POST /api/document) on an uploaded image or PDF,
   * passing the user's selected model. The backend reports `model_simulated` when the
   * requested model isn't actually loaded (falls back to CRNN) — trust that flag rather
   * than assuming based on which model was requested.
   */
  async recognize(file: File, model: OcrModelId, onUploadProgress?: (percent: number) => void): Promise<OcrResult> {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('model', model)

    const { data } = await api.post<DocumentApiResponse>('/api/document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (onUploadProgress && evt.total) onUploadProgress(Math.round((evt.loaded / evt.total) * 100))
      },
    })

    const thumbnail = await fileToDataUri(file).catch(() => undefined)

    const result: OcrResult = {
      id: uid('ocr'),
      text: data.text,
      confidence: data.avg_confidence,
      model,
      fileName: file.name,
      fileType: file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'image',
      thumbnail,
      numChars: data.num_chars,
      numLines: data.num_lines,
      timeMs: data.time_ms,
      createdAt: new Date().toISOString(),
      status: 'completed',
      modelSimulated: data.model_simulated,
    }

    mockDb.addHistory(result)
    return result
  },

  async randomSample(): Promise<{ original: string; glyph: string; translit: string; confidence: number }> {
    const { data } = await api.get('/api/random')
    return data
  },
}
