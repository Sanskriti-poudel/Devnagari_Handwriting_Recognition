import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'

export interface PaginationProps {
  page: number
  pageCount: number
  onPageChange: (page: number) => void
  className?: string
}

function getPageList(page: number, pageCount: number): (number | 'ellipsis')[] {
  if (pageCount <= 7) return Array.from({ length: pageCount }, (_, i) => i + 1)
  const pages = new Set<number>([1, pageCount, page, page - 1, page + 1])
  const sorted = Array.from(pages)
    .filter((p) => p >= 1 && p <= pageCount)
    .sort((a, b) => a - b)
  const result: (number | 'ellipsis')[] = []
  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) result.push('ellipsis')
    result.push(p)
  })
  return result
}

export function Pagination({ page, pageCount, onPageChange, className }: PaginationProps) {
  if (pageCount <= 1) return null
  return (
    <nav aria-label="Pagination" className={cn('flex items-center justify-center gap-1', className)}>
      <Button
        variant="ghost"
        size="icon"
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      {getPageList(page, pageCount).map((p, i) =>
        p === 'ellipsis' ? (
          <span key={`e-${i}`} className="flex h-9 w-9 items-center justify-center text-slate-400">
            <MoreHorizontal className="h-4 w-4" />
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            aria-current={p === page ? 'page' : undefined}
            className={cn(
              'flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium transition-all',
              p === page
                ? 'bg-gradient-brand text-white shadow-glow'
                : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/[0.06]'
            )}
          >
            {p}
          </button>
        )
      )}
      <Button
        variant="ghost"
        size="icon"
        disabled={page === pageCount}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </nav>
  )
}
