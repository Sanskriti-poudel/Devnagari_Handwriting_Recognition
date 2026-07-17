import * as ProgressPrimitive from '@radix-ui/react-progress'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface ProgressProps {
  value: number
  className?: string
  trackClassName?: string
  gradient?: boolean
  size?: 'sm' | 'md'
}

export function Progress({ value, className, trackClassName, gradient = true, size = 'md' }: ProgressProps) {
  return (
    <ProgressPrimitive.Root
      className={cn(
        'relative w-full overflow-hidden rounded-full bg-slate-100 dark:bg-white/[0.06]',
        size === 'sm' ? 'h-1.5' : 'h-2.5',
        trackClassName
      )}
    >
      <ProgressPrimitive.Indicator asChild>
        <motion.div
          className={cn('h-full rounded-full', gradient ? 'bg-gradient-brand' : 'bg-violet-500', className)}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </ProgressPrimitive.Indicator>
    </ProgressPrimitive.Root>
  )
}
