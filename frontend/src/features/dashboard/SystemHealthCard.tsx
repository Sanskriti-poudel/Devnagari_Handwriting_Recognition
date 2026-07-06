import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { useHealth } from '@/hooks/useDashboard'
import { cn } from '@/lib/utils'

const STATUS_CONFIG = {
  operational: { icon: CheckCircle2, color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10' },
  degraded: { icon: AlertTriangle, color: 'text-amber-500 bg-amber-50 dark:bg-amber-500/10' },
  down: { icon: XCircle, color: 'text-rose-500 bg-rose-50 dark:bg-rose-500/10' },
} as const

export function SystemHealthCard() {
  const { data: health, isLoading } = useHealth()

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health</CardTitle>
      </CardHeader>
      {isLoading || !health ? (
        <Skeleton className="h-8 w-full" />
      ) : (
        <div className="flex items-center gap-3">
          <span className={cn('flex h-9 w-9 items-center justify-center rounded-full', STATUS_CONFIG[health.status].color)}>
            {(() => {
              const Icon = STATUS_CONFIG[health.status].icon
              return <Icon className="h-5 w-5" />
            })()}
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{health.message}</p>
            <p className="text-xs text-slate-400">Checked {new Date(health.checkedAt).toLocaleTimeString()}</p>
          </div>
        </div>
      )}
    </Card>
  )
}
