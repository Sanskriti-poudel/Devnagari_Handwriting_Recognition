import type { HistoryFilters, OcrResult, PaginatedResult, User } from '@/types'

const KEYS = {
  users: 'devnagari-ocr-mock-users',
  session: 'devnagari-ocr-mock-session',
  history: 'devnagari-ocr-mock-history',
} as const

interface StoredUser extends User {
  password: string
}

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function write<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value))
}

function uid(prefix = 'id') {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}${Math.random().toString(36).slice(2, 6)}`
}

const DEMO_USER: StoredUser = {
  id: 'user_demo',
  fullName: 'Savyata Poudel',
  email: 'savyata@example.com',
  password: 'password123',
  university: 'Tribhuvan University',
  role: 'Final Year Student',
  createdAt: new Date('2025-01-15').toISOString(),
}

const SAMPLE_TEXTS = [
  'नेपाल एक स्वतन्त्र देश हो । यहाँका नागरिकलाई शिक्षा, स्वास्थ्य र रोजगारीको अवसर प्रदान गर्नु सरकारको प्रमुख दायित्व हो ।',
  'हिमालय पर्वत श्रृंखला विश्वकै अग्लो पर्वत शृंखला हो जुन नेपालको उत्तरी सीमामा फैलिएको छ ।',
  'शिक्षा नै जीवनको सबैभन्दा ठूलो सम्पत्ति हो, जसले मानिसलाई सही र गलतको पहिचान गर्न सिकाउँछ ।',
  'काठमाडौं उपत्यका सांस्कृतिक सम्पदाले भरिपूर्ण छ र यहाँ धेरै ऐतिहासिक मन्दिरहरू रहेका छन् ।',
  'परिश्रम र लगनशीलताले मानिसलाई जीवनमा सफलताको शिखरमा पुर्‍याउँछ ।',
]

function seedHistory(): OcrResult[] {
  const models: OcrResult['model'][] = ['crnn', 'transformer']
  const files = ['नेपाल-संविधान.jpg', 'हस्तलिखित-नोट.png', 'परियोजना-विवरण.pdf', 'कक्षा-नोट.jpg', 'चिठ्ठी.png']
  const now = Date.now()
  return Array.from({ length: 14 }).map((_, i) => ({
    id: uid('ocr'),
    text: SAMPLE_TEXTS[i % SAMPLE_TEXTS.length],
    confidence: Number((0.82 + Math.random() * 0.17).toFixed(4)),
    model: models[i % models.length],
    fileName: files[i % files.length],
    fileType: files[i % files.length].endsWith('.pdf') ? 'pdf' : 'image',
    numChars: 80 + Math.floor(Math.random() * 200),
    numLines: 1 + Math.floor(Math.random() * 4),
    timeMs: 220 + Math.floor(Math.random() * 900),
    createdAt: new Date(now - i * 1000 * 60 * 60 * (6 + Math.random() * 20)).toISOString(),
    status: 'completed' as const,
  }))
}

function ensureSeeded() {
  const users = read<StoredUser[]>(KEYS.users, [])
  if (users.length === 0) {
    write(KEYS.users, [DEMO_USER])
  }
  const history = read<OcrResult[] | null>(KEYS.history, null)
  if (history === null) {
    write(KEYS.history, seedHistory())
  }
}

ensureSeeded()

export const mockDb = {
  findUserByEmail(email: string): StoredUser | undefined {
    return read<StoredUser[]>(KEYS.users, []).find((u) => u.email.toLowerCase() === email.toLowerCase())
  },

  createUser(fullName: string, email: string, password: string): User {
    const users = read<StoredUser[]>(KEYS.users, [])
    if (users.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
      throw new Error('An account with this email already exists.')
    }
    const user: StoredUser = {
      id: uid('user'),
      fullName,
      email,
      password,
      role: 'Student',
      createdAt: new Date().toISOString(),
    }
    write(KEYS.users, [...users, user])
    return stripPassword(user)
  },

  updateUser(id: string, patch: Partial<User>): User {
    const users = read<StoredUser[]>(KEYS.users, [])
    const idx = users.findIndex((u) => u.id === id)
    if (idx === -1) throw new Error('User not found.')
    users[idx] = { ...users[idx], ...patch }
    write(KEYS.users, users)
    return stripPassword(users[idx])
  },

  changePassword(id: string, currentPassword: string, newPassword: string) {
    const users = read<StoredUser[]>(KEYS.users, [])
    const idx = users.findIndex((u) => u.id === id)
    if (idx === -1) throw new Error('User not found.')
    if (users[idx].password !== currentPassword) throw new Error('Current password is incorrect.')
    users[idx].password = newPassword
    write(KEYS.users, users)
  },

  deleteUser(id: string) {
    write(
      KEYS.users,
      read<StoredUser[]>(KEYS.users, []).filter((u) => u.id !== id)
    )
  },

  setSession(userId: string | null) {
    write(KEYS.session, userId)
  },

  getSessionUser(): User | undefined {
    const id = read<string | null>(KEYS.session, null)
    if (!id) return undefined
    const user = read<StoredUser[]>(KEYS.users, []).find((u) => u.id === id)
    return user ? stripPassword(user) : undefined
  },

  listHistory(filters: HistoryFilters): PaginatedResult<OcrResult> {
    let items = read<OcrResult[]>(KEYS.history, [])

    if (filters.search.trim()) {
      const q = filters.search.trim().toLowerCase()
      items = items.filter(
        (item) => item.fileName.toLowerCase().includes(q) || item.text.toLowerCase().includes(q)
      )
    }
    if (filters.model !== 'all') items = items.filter((item) => item.model === filters.model)
    if (filters.status !== 'all') items = items.filter((item) => item.status === filters.status)

    items = [...items].sort((a, b) => {
      let cmp = 0
      if (filters.sortBy === 'date') cmp = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
      if (filters.sortBy === 'confidence') cmp = a.confidence - b.confidence
      if (filters.sortBy === 'name') cmp = a.fileName.localeCompare(b.fileName)
      return filters.sortDir === 'asc' ? cmp : -cmp
    })

    const total = items.length
    const start = (filters.page - 1) * filters.pageSize
    return { items: items.slice(start, start + filters.pageSize), total, page: filters.page, pageSize: filters.pageSize }
  },

  addHistory(result: OcrResult) {
    const items = read<OcrResult[]>(KEYS.history, [])
    write(KEYS.history, [result, ...items])
  },

  removeHistory(id: string) {
    write(
      KEYS.history,
      read<OcrResult[]>(KEYS.history, []).filter((item) => item.id !== id)
    )
  },

  allHistory(): OcrResult[] {
    return read<OcrResult[]>(KEYS.history, [])
  },
}

function stripPassword(user: StoredUser): User {
  const rest = { ...user } as Partial<StoredUser>
  delete rest.password
  return rest as User
}
