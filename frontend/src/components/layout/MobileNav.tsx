import { NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ScanText } from 'lucide-react'
import { MOBILE_NAV_ITEMS } from '@/components/layout/navItems'
import { cn } from '@/lib/utils'

export function MobileNav() {
  const navigate = useNavigate()
  const [left, right] = [MOBILE_NAV_ITEMS.slice(0, 2), MOBILE_NAV_ITEMS.slice(2)]

  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 flex h-16 items-center justify-around border-t border-slate-200 bg-white/90 px-2 backdrop-blur-xl dark:border-white/10 dark:bg-[#0c0c11]/90 lg:hidden">
      {left.map((item) => (
        <NavItem key={item.to} to={item.to} label={item.label} Icon={item.icon} />
      ))}

      <motion.button
        whileTap={{ scale: 0.9 }}
        onClick={() => navigate('/ocr')}
        aria-label="Quick OCR"
        className="relative -mt-8 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-brand text-white shadow-glow"
      >
        <ScanText className="h-6 w-6" />
      </motion.button>

      {right.map((item) => (
        <NavItem key={item.to} to={item.to} label={item.label} Icon={item.icon} />
      ))}
    </nav>
  )
}

function NavItem({ to, label, Icon }: { to: string; label: string; Icon: React.ComponentType<{ className?: string }> }) {
  return (
    <NavLink to={to} className="flex flex-1 flex-col items-center gap-1 py-1.5 text-[11px]">
      {({ isActive }) => (
        <>
          <Icon className={cn('h-5 w-5 transition-colors', isActive ? 'text-violet-600 dark:text-violet-400' : 'text-slate-400')} />
          <span className={cn('font-medium transition-colors', isActive ? 'text-violet-600 dark:text-violet-400' : 'text-slate-400')}>
            {label}
          </span>
        </>
      )}
    </NavLink>
  )
}
