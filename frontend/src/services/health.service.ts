import { api, USE_MOCK_API } from '@/services/api'
import { modelsService } from '@/services/models.service'
import type { HealthStatus } from '@/types'

export const healthService = {
  async getHealth(): Promise<HealthStatus> {
    const models = await modelsService.list()

    if (USE_MOCK_API) {
      let reachable = true
      try {
        await api.get('/', { timeout: 4000 })
      } catch {
        reachable = false
      }
      return {
        status: reachable ? 'operational' : 'degraded',
        message: reachable ? 'All systems operational' : 'OCR backend is unreachable — check VITE_API_URL',
        models,
        checkedAt: new Date().toISOString(),
      }
    }

    try {
      const { data } = await api.get<HealthStatus>('/health')
      return data
    } catch {
      return {
        status: 'down',
        message: 'Could not reach the health endpoint.',
        models,
        checkedAt: new Date().toISOString(),
      }
    }
  },
}
