export type OcrModelId = 'crnn' | 'transformer'

export interface OcrModel {
  id: OcrModelId
  name: string
  description: string
  status: 'active' | 'inactive' | 'degraded'
}

export interface OcrResult {
  id: string
  text: string
  confidence: number
  model: OcrModelId
  fileName: string
  fileType: 'image' | 'pdf'
  thumbnail?: string
  numChars?: number
  numLines?: number
  timeMs?: number
  createdAt: string
  status: 'completed' | 'failed'
  modelSimulated?: boolean
}

export interface HistoryFilters {
  search: string
  model: OcrModelId | 'all'
  status: 'all' | 'completed' | 'failed'
  sortBy: 'date' | 'confidence' | 'name'
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface DashboardStats {
  totalDocuments: number
  totalDocumentsDelta: number
  totalRecognitions: number
  totalRecognitionsDelta: number
  avgConfidence: number
  avgConfidenceDelta: number
  totalCharacters: number
  totalCharactersDelta: number
  confidenceTrend: { label: string; value: number }[]
  storageUsedBytes: number
  storageTotalBytes: number
}

export interface HealthStatus {
  status: 'operational' | 'degraded' | 'down'
  message: string
  models: OcrModel[]
  checkedAt: string
}

export interface ActivityItem {
  id: string
  type: 'ocr' | 'login' | 'settings' | 'account'
  message: string
  createdAt: string
}

export type ThemePreference = 'light' | 'dark' | 'system'

export interface User {
  id: string
  fullName: string
  email: string
  university?: string
  role: string
  avatarUrl?: string
  createdAt: string
}

export interface AuthCredentials {
  email: string
  password: string
  remember?: boolean
}

export interface SignupPayload {
  fullName: string
  email: string
  password: string
}

export interface AppSettings {
  apiBaseUrl: string
  language: 'en' | 'ne'
  notifications: {
    email: boolean
    push: boolean
    ocrComplete: boolean
    weeklySummary: boolean
  }
  defaultModel: OcrModelId
  downloadFormat: 'txt' | 'pdf'
  privacy: {
    storeHistory: boolean
    shareAnalytics: boolean
  }
}
