import { useState } from 'react'
import { Download, Eye, FileImage, Trash2 } from 'lucide-react'
import { SkeletonText } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Tooltip } from '@/components/ui/Tooltip'
import { EmptyState } from '@/components/common/EmptyState'
import { ModelBadge } from '@/features/ocr/ModelBadge'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { formatDateTime } from '@/lib/utils'
import { downloadTextFile } from '@/lib/export'
import { useDeleteHistory } from '@/hooks/useHistory'
import { toast } from '@/components/ui/Toast'
import type { OcrResult } from '@/types'

export interface HistoryListProps {
  items: OcrResult[]
  isLoading: boolean
  onPreview: (item: OcrResult) => void
}

export function HistoryList({ items, isLoading, onPreview }: HistoryListProps) {
  const [pendingDelete, setPendingDelete] = useState<OcrResult | null>(null)
  const { mutate: deleteItem, isPending: isDeleting } = useDeleteHistory()

  const handleConfirmDelete = () => {
    if (!pendingDelete) return
    deleteItem(pendingDelete.id, {
      onSuccess: () => {
        toast.success('Deleted', `${pendingDelete.fileName} was removed from your history.`)
        setPendingDelete(null)
      },
      onError: (err) => toast.error('Could not delete', err.message),
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonText key={i} lines={1} />
        ))}
      </div>
    )
  }

  if (!items.length) {
    return (
      <EmptyState
        icon={<FileImage className="h-6 w-6" />}
        title="No results found"
        description="Try adjusting your search or filters, or run a new recognition."
      />
    )
  }

  return (
    <>
      {/* Desktop table */}
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-400 dark:border-white/10">
              <th className="px-4 py-3 font-medium">Document</th>
              <th className="px-4 py-3 font-medium">Model</th>
              <th className="px-4 py-3 font-medium">Confidence</th>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                className="border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50 dark:border-white/[0.05] dark:hover:bg-white/[0.03]"
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100 dark:bg-white/[0.06]">
                      {item.thumbnail ? (
                        <img src={item.thumbnail} alt="" className="h-full w-full object-cover" />
                      ) : (
                        <FileImage className="h-4 w-4 text-slate-400" />
                      )}
                    </div>
                    <span className="max-w-[12rem] truncate font-medium text-slate-800 dark:text-slate-100">{item.fileName}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <ModelBadge model={item.model} />
                </td>
                <td className="px-4 py-3 font-semibold text-emerald-500">{(item.confidence * 100).toFixed(1)}%</td>
                <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{formatDateTime(item.createdAt)}</td>
                <td className="px-4 py-3">
                  <Badge variant={item.status === 'completed' ? 'emerald' : 'rose'} dot>
                    {item.status}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <Tooltip content="Preview">
                      <Button variant="ghost" size="icon" onClick={() => onPreview(item)} aria-label="Preview">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </Tooltip>
                    <Tooltip content="Download TXT">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => downloadTextFile(item.text, `${item.fileName}.txt`)}
                        aria-label="Download"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </Tooltip>
                    <Tooltip content="Delete">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setPendingDelete(item)}
                        aria-label="Delete"
                        className="hover:text-rose-500"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </Tooltip>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="space-y-3 md:hidden">
        {items.map((item) => (
          <div key={item.id} className="rounded-xl border border-slate-200 p-3.5 dark:border-white/10">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-100 dark:bg-white/[0.06]">
                {item.thumbnail ? (
                  <img src={item.thumbnail} alt="" className="h-full w-full object-cover" />
                ) : (
                  <FileImage className="h-4 w-4 text-slate-400" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">{item.fileName}</p>
                <p className="text-xs text-slate-400">{formatDateTime(item.createdAt)}</p>
              </div>
              <span className="text-sm font-bold text-emerald-500">{(item.confidence * 100).toFixed(1)}%</span>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ModelBadge model={item.model} />
                <Badge variant={item.status === 'completed' ? 'emerald' : 'rose'} dot>
                  {item.status}
                </Badge>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" onClick={() => onPreview(item)} aria-label="Preview">
                  <Eye className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => downloadTextFile(item.text, `${item.fileName}.txt`)} aria-label="Download">
                  <Download className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => setPendingDelete(item)} aria-label="Delete" className="hover:text-rose-500">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <ConfirmDialog
        open={!!pendingDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title="Delete this recognition?"
        description={`"${pendingDelete?.fileName}" will be permanently removed from your history.`}
        confirmLabel="Delete"
        loading={isDeleting}
        onConfirm={handleConfirmDelete}
      />
    </>
  )
}
