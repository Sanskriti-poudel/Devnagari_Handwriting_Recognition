import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva('inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium', {
  variants: {
    variant: {
      default: 'bg-slate-100 text-slate-700 dark:bg-white/[0.06] dark:text-slate-300',
      indigo: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-300',
      violet: 'bg-violet-50 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300',
      cyan: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300',
      emerald: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300',
      amber: 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300',
      rose: 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300',
      outline: 'border border-slate-200 text-slate-600 dark:border-white/10 dark:text-slate-300',
    },
  },
  defaultVariants: { variant: 'default' },
})

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  dot?: boolean
}

export function Badge({ className, variant, dot, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props}>
      {dot && (
        <span
          className={cn('h-1.5 w-1.5 rounded-full', {
            'bg-slate-500': !variant || variant === 'default' || variant === 'outline',
            'bg-indigo-500': variant === 'indigo',
            'bg-violet-500': variant === 'violet',
            'bg-cyan-500': variant === 'cyan',
            'bg-emerald-500': variant === 'emerald',
            'bg-amber-500': variant === 'amber',
            'bg-rose-500': variant === 'rose',
          })}
        />
      )}
      {children}
    </span>
  )
}
