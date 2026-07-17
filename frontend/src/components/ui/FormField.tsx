import * as React from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface FormFieldProps {
  label?: string
  htmlFor?: string
  error?: string
  hint?: string
  className?: string
  children: React.ReactNode
  action?: React.ReactNode
}

export function FormField({ label, htmlFor, error, hint, className, children, action }: FormFieldProps) {
  return (
    <div className={cn('space-y-1.5', className)}>
      {(label || action) && (
        <div className="flex items-center justify-between">
          {label && (
            <label htmlFor={htmlFor} className="text-sm font-medium text-slate-700 dark:text-slate-300">
              {label}
            </label>
          )}
          {action}
        </div>
      )}
      {children}
      <AnimatePresence mode="wait">
        {error ? (
          <motion.p
            key="error"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            className="text-xs font-medium text-rose-500"
            role="alert"
          >
            {error}
          </motion.p>
        ) : hint ? (
          <p className="text-xs text-slate-400">{hint}</p>
        ) : null}
      </AnimatePresence>
    </div>
  )
}
