import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Progress } from '@/components/ui/Progress'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatBytes } from '@/lib/utils'

export function StorageUsageCard({ usedBytes, totalBytes, isLoading }: { usedBytes: number; totalBytes: number; isLoading?: boolean }) {
  const percent = totalBytes ? Math.round((usedBytes / totalBytes) * 100) : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Storage Usage</CardTitle>
      </CardHeader>
      {isLoading ? (
        <Skeleton className="h-8 w-full" />
      ) : (
        <>
          <div className="mb-2 flex items-end justify-between">
            <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">
              {formatBytes(usedBytes)} <span className="font-normal text-slate-400">/ {formatBytes(totalBytes)}</span>
            </span>
            <span className="text-xs font-semibold text-violet-500">{percent}%</span>
          </div>
          <Progress value={percent} />
        </>
      )}
    </Card>
  )
}
