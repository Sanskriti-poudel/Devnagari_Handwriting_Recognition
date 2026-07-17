import * as React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          'w-full rounded-xl border bg-white px-3.5 py-3 text-sm text-slate-900 outline-none transition-all duration-200 placeholder:text-slate-400',
          'focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10',
          'dark:bg-white/[0.04] dark:text-slate-100 dark:placeholder:text-slate-500',
          error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/10' : 'border-slate-200 dark:border-white/10',
          className
        )}
        {...props}
      />
    )
  }
)
Textarea.displayName = 'Textarea'
