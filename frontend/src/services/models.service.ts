import { api, USE_MOCK_API } from '@/services/api'
import { sleep } from '@/lib/utils'
import type { OcrModel } from '@/types'

const FALLBACK_MODELS: OcrModel[] = [
  {
    id: 'crnn',
    name: 'CRNN (CNN + RNN + CTC)',
    description: 'Better for character-level recognition',
    status: 'active',
  },
  {
    id: 'transformer',
    name: 'Transformer (TrOCR)',
    description: 'Better for word & line recognition',
    status: 'active',
  },
]

export const modelsService = {
  async list(): Promise<OcrModel[]> {
    if (USE_MOCK_API) {
      await sleep(150)
      return FALLBACK_MODELS
    }
    try {
      const { data } = await api.get<OcrModel[]>('/models')
      return data
    } catch {
      return FALLBACK_MODELS
    }
  },
}
