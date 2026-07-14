import { api } from '@/services/api'
import type { DocumentOcrResponse, DocumentPageResult, ExportFormat, OcrModelId } from '@/types'

interface DocumentPageResultRaw {
  annotated?: string
  text: string
  num_lines: number
  num_chars: number
  avg_confidence: number
}

interface DocumentOcrResponseRaw {
  doc_id: string
  engine: string
  text: string
  num_chars: number
  num_lines: number
  num_pages: number
  avg_confidence: number
  time_ms: number
  annotated?: string
  pages: DocumentPageResultRaw[]
}

function mapPage(p: DocumentPageResultRaw): DocumentPageResult {
  return {
    annotated: p.annotated,
    text: p.text,
    numLines: p.num_lines,
    numChars: p.num_chars,
    avgConfidence: p.avg_confidence,
  }
}

function mapResponse(raw: DocumentOcrResponseRaw): DocumentOcrResponse {
  return {
    docId: raw.doc_id,
    engine: raw.engine,
    text: raw.text,
    numChars: raw.num_chars,
    numLines: raw.num_lines,
    numPages: raw.num_pages,
    avgConfidence: raw.avg_confidence,
    timeMs: raw.time_ms,
    annotated: raw.annotated,
    pages: raw.pages.map(mapPage),
  }
}

export const documentService = {
  /**
   * Multi-page document OCR (kept separate from ocrService.recognize, which
   * persists a single flattened result to history/dashboard). Returns per-page
   * text + a doc_id used by exportDocument's "pdf" format to rebuild a
   * searchable PDF from the cached page images + line boxes.
   */
  async recognizePages(file: File, _model: OcrModelId): Promise<DocumentOcrResponse> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post<DocumentOcrResponseRaw>('/api/document/pages', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return mapResponse(data)
  },

  async exportDocument(format: ExportFormat, text: string, docId?: string): Promise<Blob> {
    const { data } = await api.post(
      '/api/export',
      { format, text, doc_id: docId },
      { responseType: 'blob' }
    )
    return data as Blob
  },
}
