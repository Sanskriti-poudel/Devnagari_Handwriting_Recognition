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
}

export const ocrService = {
  /**
   * Runs the real, trained CRNN backend (webapp/server.py: POST /api/document) on an
   * uploaded image or PDF. The backend only ships one recognizer today, so selecting
   * "Transformer" in the UI still calls the same real model — the result is flagged
   * `modelSimulated` so the UI can be upfront about it instead of pretending.
   */
  async recognize(file: File, model: OcrModelId, onUploadProgress?: (percent: number) => void): Promise<OcrResult> {
    const formData = new FormData()
    formData.append('image', file)

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
      modelSimulated: model === 'transformer',
    }

    mockDb.addHistory(result)
    return result
  },

  async randomSample(): Promise<{ original: string; glyph: string; translit: string; confidence: number }> {
    const { data } = await api.get('/api/random')
    return data
  },
}
