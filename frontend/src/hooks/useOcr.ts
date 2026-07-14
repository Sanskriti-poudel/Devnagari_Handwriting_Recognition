import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ocrService } from '@/services/ocr.service'
import { documentService } from '@/services/document.service'
import type { OcrModelId } from '@/types'

export function useRecognize(onUploadProgress?: (percent: number) => void) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, model }: { file: File; model: OcrModelId }) =>
      ocrService.recognize(file, model, onUploadProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

/**
 * Multi-page document OCR (PDFs) — kept separate from useRecognize since it
 * doesn't persist to history/dashboard and returns per-page text + a doc_id
 * for exporting a searchable PDF, rather than a single flattened OcrResult.
 */
export function useRecognizeDocument() {
  return useMutation({
    mutationFn: ({ file, model }: { file: File; model: OcrModelId }) =>
      documentService.recognizePages(file, model),
  })
}
