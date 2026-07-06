import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { useModels } from '@/hooks/useModels'
import { cn } from '@/lib/utils'

export function ModelStatusCard() {
  const { data: models, isLoading } = useModels()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model Status</CardTitle>
      </CardHeader>
      <div className="space-y-3">
        {isLoading
          ? Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-5 w-full" />)
          : models?.map((model) => (
              <div key={model.id} className="flex items-center justify-between text-sm">
                <span className="text-slate-600 dark:text-slate-300">{model.name.split(' (')[0]} Model</span>
                <span
                  className={cn(
                    'inline-flex items-center gap-1.5 text-xs font-semibold',
                    model.status === 'active' ? 'text-emerald-500' : 'text-slate-400'
                  )}
                >
                  <span
                    className={cn(
                      'h-1.5 w-1.5 rounded-full',
                      model.status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'
                    )}
                  />
                  {model.status === 'active' ? 'Active' : 'Inactive'}
                </span>
              </div>
            ))}
      </div>
    </Card>
  )
}
