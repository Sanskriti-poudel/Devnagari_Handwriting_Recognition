import { useState } from 'react'
import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { Card } from '@/components/ui/Card'
import { Pagination } from '@/components/ui/Pagination'
import { PageTransition } from '@/components/common/PageTransition'
import { HistoryToolbar } from '@/features/history/HistoryToolbar'
import { HistoryList } from '@/features/history/HistoryList'
import { HistoryPreviewModal } from '@/features/history/HistoryPreviewModal'
import { useHistoryList } from '@/hooks/useHistory'
import type { HistoryFilters, OcrResult } from '@/types'

const DEFAULT_FILTERS: HistoryFilters = {
  search: '',
  model: 'all',
  status: 'all',
  sortBy: 'date',
  sortDir: 'desc',
  page: 1,
  pageSize: 8,
}

export default function HistoryPage() {
  const [filters, setFilters] = useState<HistoryFilters>(DEFAULT_FILTERS)
  const [preview, setPreview] = useState<OcrResult | null>(null)
  const { data, isLoading } = useHistoryList(filters)

  const patchFilters = (patch: Partial<HistoryFilters>) => setFilters((f) => ({ ...f, ...patch }))
  const pageCount = data ? Math.max(1, Math.ceil(data.total / data.pageSize)) : 1

  return (
    <PageTransition>
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <Breadcrumb items={[{ label: 'History' }]} />
          <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">OCR History</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Browse, search, and manage every document you've recognized.
          </p>
        </div>

        <Card>
          <HistoryToolbar filters={filters} onChange={patchFilters} />
        </Card>

        <Card className="p-0 sm:p-0">
          <div className="p-4 sm:p-2">
            <HistoryList items={data?.items ?? []} isLoading={isLoading} onPreview={setPreview} />
          </div>
        </Card>

        {data && data.total > 0 && (
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <p className="text-xs text-slate-400">
              Showing {(filters.page - 1) * filters.pageSize + 1}–{Math.min(filters.page * filters.pageSize, data.total)} of {data.total}
            </p>
            <Pagination page={filters.page} pageCount={pageCount} onPageChange={(page) => patchFilters({ page })} />
          </div>
        )}
      </div>

      <HistoryPreviewModal item={preview} onClose={() => setPreview(null)} />
    </PageTransition>
  )
}
