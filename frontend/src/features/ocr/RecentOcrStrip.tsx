import { Link } from 'react-router-dom'
import { FileImage } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { useHistoryList } from '@/hooks/useHistory'

export function RecentOcrStrip() {
  const { data, isLoading } = useHistoryList({
    search: '',
    model: 'all',
    status: 'all',
    sortBy: 'date',
    sortDir: 'desc',
    page: 1,
    pageSize: 6,
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent OCR History</CardTitle>
        <Link to="/history" className="text-xs font-semibold text-violet-600 hover:underline dark:text-violet-400">
          View All →
        </Link>
      </CardHeader>

      {isLoading ? (
        <div className="flex gap-3 overflow-hidden">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-24 shrink-0 rounded-xl" />
          ))}
        </div>
      ) : !data?.items.length ? (
        <EmptyState icon={<FileImage className="h-6 w-6" />} title="No history yet" description="Recognized documents will appear here." />
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-1">
          {data.items.map((item) => (
            <div
              key={item.id}
              className="group relative h-24 w-24 shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-100 transition-transform hover:-translate-y-1 dark:border-white/10 dark:bg-white/[0.04]"
            >
              {item.thumbnail ? (
                <img src={item.thumbnail} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-slate-400">
                  <FileImage className="h-6 w-6" />
                </div>
              )}
              <span className="absolute bottom-1 right-1 rounded-md bg-slate-900/80 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                {(item.confidence * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
