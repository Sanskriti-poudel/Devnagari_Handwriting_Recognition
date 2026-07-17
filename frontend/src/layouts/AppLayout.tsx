import { Suspense, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Sidebar } from '@/components/layout/Sidebar'
import { Topbar } from '@/components/layout/Topbar'
import { MobileNav } from '@/components/layout/MobileNav'
import { Footer } from '@/components/layout/Footer'
import { Drawer } from '@/components/ui/Drawer'
import { NAV_ITEMS } from '@/components/layout/navItems'
import { Logo } from '@/components/layout/Logo'
import { NavLink } from 'react-router-dom'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { Loader } from '@/components/ui/Loader'
import { cn } from '@/lib/utils'

export function AppLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-surface-light dark:bg-surface-dark">
      <Sidebar />

      <Drawer open={mobileNavOpen} onOpenChange={setMobileNavOpen} title={<Logo iconOnly={false} />}>
        <nav className="mt-2 flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMobileNavOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-gradient-brand text-white shadow-glow'
                    : 'text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/[0.06]'
                )
              }
            >
              <item.icon className="h-[18px] w-[18px]" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </Drawer>

      <div className="flex min-h-screen flex-1 flex-col overflow-x-hidden">
        <Topbar onOpenMobileNav={() => setMobileNavOpen(true)} />
        <main className="flex-1 px-4 pb-24 pt-6 sm:px-6 lg:pb-8">
          <ErrorBoundary>
            <Suspense
              fallback={
                <div className="flex h-[50vh] items-center justify-center text-violet-500">
                  <Loader size={32} />
                </div>
              }
            >
              <AnimatePresence mode="wait">
                <Outlet />
              </AnimatePresence>
            </Suspense>
          </ErrorBoundary>
        </main>
        <div className="hidden lg:block">
          <Footer />
        </div>
        <MobileNav />
      </div>
    </div>
  )
}
