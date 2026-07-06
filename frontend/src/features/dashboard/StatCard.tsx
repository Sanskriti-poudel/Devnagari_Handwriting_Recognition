import type { LucideIcon } from 'lucide-react'
import { TrendingDown, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'
import { Card } from '@/components/ui/Card'
import { AnimatedNumber } from '@/components/common/AnimatedNumber'
import { staggerItem } from '@/components/common/PageTransition'
import { cn } from '@/lib/utils'

export interface StatCardProps {
  icon: LucideIcon
  label: string
  value: number
  decimals?: number
  suffix?: string
  delta: number
  tone: 'indigo' | 'violet' | 'emerald' | 'rose'
}

const TONE_STYLES: Record<StatCardProps['tone'], string> = {
  indigo: 'bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400',
  violet: 'bg-violet-50 text-violet-600 dark:bg-violet-500/10 dark:text-violet-400',
  emerald: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400',
  rose: 'bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400',
}

export function StatCard({ icon: Icon, label, value, decimals = 0, suffix = '', delta, tone }: StatCardProps) {
  const positive = delta >= 0
  return (
    <Card hover variants={staggerItem}>
      <div className="flex items-center gap-3">
        <div className={cn('flex h-11 w-11 shrink-0 items-center justify-center rounded-xl', TONE_STYLES[tone])}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium text-slate-400">{label}</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white">
            <AnimatedNumber value={value} decimals={decimals} suffix={suffix} />
          </p>
        </div>
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className={cn(
          'mt-3 inline-flex items-center gap-1 text-xs font-semibold',
          positive ? 'text-emerald-500' : 'text-rose-500'
        )}
      >
        {positive ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
        {Math.abs(delta)}% from last month
      </motion.div>
    </Card>
  )
}
