import * as React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
  icon?: React.ReactNode
  endAdornment?: React.ReactNode
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, icon, endAdornment, ...props }, ref) => {
    return (
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">{icon}</span>
        )}
        <input
          ref={ref}
          className={cn(
            'h-11 w-full rounded-xl border bg-white px-3.5 text-sm text-slate-900 outline-none transition-all duration-200 placeholder:text-slate-400',
            'focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10',
            'dark:bg-white/[0.04] dark:text-slate-100 dark:placeholder:text-slate-500',
            error
              ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/10'
              : 'border-slate-200 dark:border-white/10',
            icon && 'pl-10',
            endAdornment && 'pr-10',
            className
          )}
          {...props}
        />
        {endAdornment && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">{endAdornment}</span>
        )}
      </div>
    )
  }
)
Input.displayName = 'Input'
