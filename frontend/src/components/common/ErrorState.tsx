import { AlertOctagon, RotateCcw } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

export interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  description = "We couldn't complete that request. Please try again.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center px-6 py-16 text-center', className)}>
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-50 text-rose-500 dark:bg-rose-500/10 dark:text-rose-400"
      >
        <AlertOctagon className="h-7 w-7" />
      </motion.div>
      <h3 className="text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-5" onClick={onRetry}>
          <RotateCcw className="h-3.5 w-3.5" /> Try again
        </Button>
      )}
    </div>
  )
}
