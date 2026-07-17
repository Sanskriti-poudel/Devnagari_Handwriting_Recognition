import { LayoutDashboard, ScanText, History, Cpu, User, Settings } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
}

export const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'OCR', to: '/ocr', icon: ScanText },
  { label: 'History', to: '/history', icon: History },
  { label: 'Models', to: '/models', icon: Cpu },
  { label: 'Profile', to: '/profile', icon: User },
  { label: 'Settings', to: '/settings', icon: Settings },
]

export const MOBILE_NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'OCR', to: '/ocr', icon: ScanText },
  { label: 'History', to: '/history', icon: History },
  { label: 'Profile', to: '/profile', icon: User },
]
