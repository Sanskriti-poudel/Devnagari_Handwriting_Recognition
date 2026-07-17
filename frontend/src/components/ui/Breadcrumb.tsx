import { Fragment } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface BreadcrumbItem {
  label: string
  href?: string
}

export function Breadcrumb({ items, className }: { items: BreadcrumbItem[]; className?: string }) {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center gap-1.5 text-sm', className)}>
      <Link to="/dashboard" className="text-slate-400 transition-colors hover:text-violet-600 dark:hover:text-violet-400">
        <Home className="h-3.5 w-3.5" />
      </Link>
      {items.map((item, i) => (
        <Fragment key={item.label}>
          <ChevronRight className="h-3.5 w-3.5 text-slate-300 dark:text-slate-600" />
          {item.href && i !== items.length - 1 ? (
            <Link to={item.href} className="text-slate-500 transition-colors hover:text-violet-600 dark:hover:text-violet-400">
              {item.label}
            </Link>
          ) : (
            <span className="font-medium text-slate-900 dark:text-white">{item.label}</span>
          )}
        </Fragment>
      ))}
    </nav>
  )
}
