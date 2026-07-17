import { useNavigate } from 'react-router-dom'
import { Bell, LogOut, Menu, Search, Settings, User as UserIcon } from 'lucide-react'
import { ThemeToggle } from '@/components/layout/ThemeToggle'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import {
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownLabel,
  DropdownSeparator,
  DropdownTrigger,
} from '@/components/ui/Dropdown'
import { useAuthStore } from '@/stores/auth.store'
import { toast } from '@/components/ui/Toast'

const NOTIFICATIONS = [
  { id: 1, text: 'Your document "नेपाल-संविधान.jpg" was recognized at 98.7% confidence.', time: '2h ago' },
  { id: 2, text: 'Weekly summary: 42 documents processed this week.', time: '1d ago' },
  { id: 3, text: 'New Transformer (TrOCR) model track is in training.', time: '3d ago' },
]

export function Topbar({ onOpenMobileNav }: { onOpenMobileNav?: () => void }) {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const handleLogout = async () => {
    await logout()
    toast.success('Signed out', 'See you again soon.')
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/80 px-4 backdrop-blur-xl dark:border-white/10 dark:bg-surface-dark/80 sm:px-6">
      <button
        onClick={onOpenMobileNav}
        className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/[0.06] lg:hidden"
        aria-label="Open navigation menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="relative hidden max-w-sm flex-1 sm:block">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          placeholder="Search anything..."
          aria-label="Search"
          className="h-10 w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-14 text-sm text-slate-900 outline-none transition-all focus:border-violet-500 focus:bg-white focus:ring-4 focus:ring-violet-500/10 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-100 dark:focus:bg-white/[0.06]"
        />
        <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-400 dark:border-white/10 dark:bg-white/[0.06]">
          ⌘K
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-1.5 sm:gap-2.5">
        <Dropdown>
          <DropdownTrigger className="relative rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.06] dark:hover:text-white">
            <Bell className="h-5 w-5" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-white dark:ring-surface-dark" />
          </DropdownTrigger>
          <DropdownContent className="w-80">
            <DropdownLabel>Notifications</DropdownLabel>
            {NOTIFICATIONS.map((n) => (
              <DropdownItem key={n.id} className="flex-col items-start gap-0.5">
                <p className="text-slate-700 dark:text-slate-200">{n.text}</p>
                <span className="text-xs text-slate-400">{n.time}</span>
              </DropdownItem>
            ))}
          </DropdownContent>
        </Dropdown>

        <ThemeToggle />

        <Dropdown>
          <DropdownTrigger className="rounded-full outline-none ring-violet-500 ring-offset-2 ring-offset-white focus-visible:ring-2 dark:ring-offset-surface-dark">
            <Avatar name={user?.fullName ?? 'Guest'} src={user?.avatarUrl} size="sm" ring />
          </DropdownTrigger>
          <DropdownContent className="w-64">
            <div className="flex items-center gap-3 px-2 py-2">
              <Avatar name={user?.fullName ?? 'Guest'} src={user?.avatarUrl} size="md" />
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">{user?.fullName}</p>
                <p className="truncate text-xs text-slate-400">{user?.email}</p>
              </div>
            </div>
            <DropdownSeparator />
            <DropdownItem onClick={() => navigate('/profile')}>
              <UserIcon className="h-4 w-4" /> Profile
              <Badge variant="violet" className="ml-auto">
                {user?.role ?? 'Member'}
              </Badge>
            </DropdownItem>
            <DropdownItem onClick={() => navigate('/settings')}>
              <Settings className="h-4 w-4" /> Settings
            </DropdownItem>
            <DropdownSeparator />
            <DropdownItem onClick={handleLogout} className="text-rose-600 dark:text-rose-400">
              <LogOut className="h-4 w-4" /> Log out
            </DropdownItem>
          </DropdownContent>
        </Dropdown>
      </div>
    </header>
  )
}
