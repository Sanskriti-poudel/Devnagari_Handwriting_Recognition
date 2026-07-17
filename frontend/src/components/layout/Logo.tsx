import { cn } from '@/lib/utils'

export interface LogoProps {
  className?: string
  iconOnly?: boolean
  onDark?: boolean
}

export function Logo({ className, iconOnly = false, onDark = false }: LogoProps) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-brand font-devanagari text-lg font-bold text-white shadow-glow">
        अ
      </div>
      {!iconOnly && (
        <div className="leading-tight">
          <p className={cn('text-sm font-bold', onDark ? 'text-white' : 'text-slate-900 dark:text-white')}>
            Devanagari OCR
          </p>
          <p className={cn('text-[11px] font-medium', onDark ? 'text-white/60' : 'text-slate-400 dark:text-slate-500')}>
            AI Powered Recognition
          </p>
        </div>
      )}
    </div>
  )
}
