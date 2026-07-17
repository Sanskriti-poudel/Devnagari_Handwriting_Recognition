import * as React from 'react'
import { motion, type HTMLMotionProps } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface CardProps extends HTMLMotionProps<'div'> {
  hover?: boolean
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(({ className, hover = false, ...props }, ref) => {
  return (
    <motion.div
      ref={ref}
      className={cn(
        'card-surface p-5 transition-all duration-300',
        hover && 'hover:-translate-y-1 hover:border-violet-300/60 hover:shadow-glow dark:hover:border-violet-500/30',
        className
      )}
      {...props}
    />
  )
})
Card.displayName = 'Card'

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mb-4 flex items-center justify-between', className)} {...props} />
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('text-base font-semibold text-slate-900 dark:text-white', className)} {...props} />
}

export function CardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm text-slate-500 dark:text-slate-400', className)} {...props} />
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('', className)} {...props} />
}
