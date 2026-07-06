import { Link } from 'react-router-dom'
import { FileImage, FileText } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { SkeletonText } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ModelBadge } from '@/features/ocr/ModelBadge'
import { useHistoryList } from '@/hooks/useHistory'
import { formatDateTime } from '@/lib/utils'

export function RecentRecognitions() {
  const { data, isLoading } = useHistoryList({
    search: '',
    model: 'all',
    status: 'all',
    sortBy: 'date',
    sortDir: 'desc',
    page: 1,
    pageSize: 4,
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Recognitions</CardTitle>
        <Link to="/history" className="text-xs font-semibold text-violet-600 hover:underline dark:text-violet-400">
          View all →
        </Link>
      </CardHeader>

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonText key={i} lines={1} />
          ))}
        </div>
      ) : !data?.items.length ? (
        <EmptyState
          icon={<FileText className="h-6 w-6" />}
          title="No recognitions yet"
          description="Upload your first document to see it here."
        />
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-white/[0.06]">
          {data.items.map((item) => (
            <li key={item.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100 dark:bg-white/[0.06]">
                {item.thumbnail ? (
                  <img src={item.thumbnail} alt="" className="h-full w-full object-cover" />
                ) : (
                  <FileImage className="h-4 w-4 text-slate-400" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{item.fileName}</p>
                <p className="text-xs text-slate-400">{formatDateTime(item.createdAt)}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <span className="text-sm font-semibold text-emerald-500">{(item.confidence * 100).toFixed(1)}%</span>
                <ModelBadge model={item.model} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
