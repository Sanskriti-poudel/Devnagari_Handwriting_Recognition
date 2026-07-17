import * as React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center px-6 py-16 text-center', className)}>
      <motion.div
        className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand-soft text-violet-500 dark:text-violet-400"
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
      >
        {icon}
      </motion.div>
      <h3 className="text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
      {description && <p className="mt-1.5 max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
