import { api, USE_MOCK_API } from '@/services/api'
import { mockDb } from '@/services/mock/mockDb'
import { sleep } from '@/lib/utils'
import type { ActivityItem, DashboardStats } from '@/types'

function computeStats(): DashboardStats {
  const history = mockDb.allHistory()
  const totalDocuments = history.length
  const totalRecognitions = history.filter((h) => h.status === 'completed').length
  const avgConfidence = totalRecognitions
    ? history.reduce((sum, h) => sum + h.confidence, 0) / history.length
    : 0
  const totalCharacters = history.reduce((sum, h) => sum + (h.numChars ?? 0), 0)

  const byDay = new Map<string, { sum: number; count: number }>()
  ;[...history]
    .sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
    .forEach((item) => {
      const d = new Date(item.createdAt)
      const label = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
      const bucket = byDay.get(label) ?? { sum: 0, count: 0 }
      bucket.sum += item.confidence
      bucket.count += 1
      byDay.set(label, bucket)
    })
  const confidenceTrend = Array.from(byDay.entries()).map(([label, { sum, count }]) => ({
    label,
    value: Math.round((sum / count) * 1000) / 10,
  }))

  return {
    totalDocuments,
    totalDocumentsDelta: 18,
    totalRecognitions,
    totalRecognitionsDelta: 22,
    avgConfidence: Math.round(avgConfidence * 1000) / 10,
    avgConfidenceDelta: 3.4,
    totalCharacters,
    totalCharactersDelta: 25,
    confidenceTrend: confidenceTrend.length ? confidenceTrend : [{ label: 'Today', value: 0 }],
    storageUsedBytes: 2.4 * 1024 ** 3,
    storageTotalBytes: 10 * 1024 ** 3,
  }
}

function computeActivity(): ActivityItem[] {
  return [...mockDb.allHistory()]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 8)
    .map((item) => ({
      id: `activity_${item.id}`,
      type: 'ocr' as const,
      message: `Recognized "${item.fileName}" with ${(item.confidence * 100).toFixed(1)}% confidence`,
      createdAt: item.createdAt,
    }))
}

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    if (USE_MOCK_API) {
      await sleep(400)
      return computeStats()
    }
    const { data } = await api.get<DashboardStats>('/dashboard/stats')
    return data
  },

  async getActivity(): Promise<ActivityItem[]> {
    if (USE_MOCK_API) {
      await sleep(300)
      return computeActivity()
    }
    const { data } = await api.get<ActivityItem[]>('/dashboard/activity')
    return data
  },
}
