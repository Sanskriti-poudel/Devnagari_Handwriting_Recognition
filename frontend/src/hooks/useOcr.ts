import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ocrService } from '@/services/ocr.service'
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
