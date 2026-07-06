import { api, USE_MOCK_API } from '@/services/api'
import { mockDb } from '@/services/mock/mockDb'
import { sleep } from '@/lib/utils'
import type { HistoryFilters, OcrResult, PaginatedResult } from '@/types'

export const historyService = {
  async list(filters: HistoryFilters): Promise<PaginatedResult<OcrResult>> {
    if (USE_MOCK_API) {
      await sleep(350)
      return mockDb.listHistory(filters)
    }
    const { data } = await api.get<PaginatedResult<OcrResult>>('/history', { params: filters })
    return data
  },

  async remove(id: string): Promise<void> {
    if (USE_MOCK_API) {
      await sleep(250)
      mockDb.removeHistory(id)
      return
    }
    await api.delete(`/history/${id}`)
  },
}
