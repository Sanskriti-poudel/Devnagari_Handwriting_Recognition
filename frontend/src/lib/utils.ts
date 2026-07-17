import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatDateTime(iso: string) {
  const d = new Date(iso)
  return `${d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })} · ${d.toLocaleTimeString(
    undefined,
    { hour: 'numeric', minute: '2-digit' }
  )}`
}

export function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

export function confidenceLabel(confidence: number) {
  if (confidence >= 0.95) return { label: 'Excellent', tone: 'emerald' as const }
  if (confidence >= 0.85) return { label: 'Good', tone: 'cyan' as const }
  if (confidence >= 0.7) return { label: 'Fair', tone: 'amber' as const }
  return { label: 'Low', tone: 'rose' as const }
}

export function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function initials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('')
}
