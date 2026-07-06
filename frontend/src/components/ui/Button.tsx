import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'relative inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97] overflow-hidden select-none',
  {
    variants: {
      variant: {
        primary:
          'bg-gradient-brand bg-[length:200%_auto] text-white shadow-glow hover:bg-right hover:shadow-lg hover:-translate-y-0.5',
        secondary:
          'bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-white/[0.06] dark:text-slate-100 dark:hover:bg-white/[0.1]',
        outline:
          'border border-slate-200 bg-transparent text-slate-700 hover:border-violet-400 hover:text-violet-600 dark:border-white/10 dark:text-slate-200 dark:hover:border-violet-400 dark:hover:text-violet-300',
        ghost: 'bg-transparent text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/[0.06]',
        destructive: 'bg-rose-500 text-white hover:bg-rose-600 shadow-sm hover:shadow-md hover:-translate-y-0.5',
        link: 'text-violet-600 underline-offset-4 hover:underline dark:text-violet-400',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4',
        lg: 'h-12 px-6 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, disabled, children, onClick, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    const [ripples, setRipples] = React.useState<{ x: number; y: number; id: number }[]>([])

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      const rect = e.currentTarget.getBoundingClientRect()
      const id = Date.now()
      setRipples((prev) => [...prev, { x: e.clientX - rect.left, y: e.clientY - rect.top, id }])
      window.setTimeout(() => setRipples((prev) => prev.filter((r) => r.id !== id)), 600)
      onClick?.(e)
    }

    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={disabled || loading}
        onClick={handleClick}
        {...props}
      >
        {asChild ? (
          children
        ) : (
          <>
            {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
            {children}
            {ripples.map((r) => (
              <span
                key={r.id}
                className="pointer-events-none absolute rounded-full bg-white/40 animate-ping"
                style={{ left: r.x - 8, top: r.y - 8, width: 16, height: 16 }}
              />
            ))}
          </>
        )}
      </Comp>
    )
  }
)
Button.displayName = 'Button'
