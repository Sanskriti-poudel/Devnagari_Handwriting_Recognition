import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import { NAV_ITEMS } from '@/components/layout/navItems'
import { Logo } from '@/components/layout/Logo'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/stores/auth.store'

export function Sidebar() {
  const user = useAuthStore((s) => s.user)

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-5 dark:border-white/10 dark:bg-[#0c0c11] lg:flex">
      <div className="px-2">
        <Logo />
      </div>

      <nav className="mt-8 flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} className="relative">
            {({ isActive }) => (
              <div
                className={
                  'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors duration-200 ' +
                  (isActive
                    ? 'text-white'
                    : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white')
                }
              >
                {isActive && (
                  <motion.span
                    layoutId="sidebar-active-pill"
                    className="absolute inset-0 rounded-xl bg-gradient-brand shadow-glow"
                    transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                  />
                )}
                <item.icon
                  className="relative z-10 h-[18px] w-[18px] shrink-0 transition-transform duration-200 group-hover:scale-110"
                  strokeWidth={2}
                />
                <span className="relative z-10">{item.label}</span>
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-4">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-brand p-4 text-white shadow-glow">
          <Sparkles className="absolute -right-2 -top-2 h-16 w-16 text-white/10" />
          <p className="text-sm font-semibold">Upgrade to Pro</p>
          <p className="mt-1 text-xs text-white/80">Unlock unlimited uploads, premium models and more.</p>
          <Button size="sm" variant="secondary" className="mt-3 w-full bg-white text-violet-700 hover:bg-white/90">
            Upgrade Now
          </Button>
        </div>

        {user && (
          <div className="flex items-center gap-2.5 rounded-xl border border-slate-200 p-2.5 dark:border-white/10">
            <Avatar name={user.fullName} src={user.avatarUrl} size="sm" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-slate-900 dark:text-white">{user.fullName}</p>
              <p className="truncate text-[11px] text-slate-400">{user.email}</p>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}
