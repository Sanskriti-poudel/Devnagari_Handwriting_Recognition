import { cn } from '@/lib/utils'

export function Loader({ className, size = 24 }: { className?: string; size?: number }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn('inline-block animate-spin rounded-full border-2 border-current border-t-transparent', className)}
      style={{ width: size, height: size }}
    />
  )
}

/** A small cluster of bouncing dots, styled like an AI "thinking" indicator. */
export function NeuralDots({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5', className)} role="status" aria-label="Processing">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 animate-bounce rounded-full bg-gradient-brand"
          style={{ animationDelay: `${i * 0.15}s`, animationDuration: '1s' }}
        />
      ))}
    </span>
  )
}
