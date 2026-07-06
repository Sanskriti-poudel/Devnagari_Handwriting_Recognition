import { useState } from 'react'
import { Check, Copy, Download, FileDown, FileImage } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { ModelBadge } from '@/features/ocr/ModelBadge'
import { formatDateTime } from '@/lib/utils'
import { downloadTextAsPdf, downloadTextFile } from '@/lib/export'
import { toast } from '@/components/ui/Toast'
import type { OcrResult } from '@/types'

export function HistoryPreviewModal({ item, onClose }: { item: OcrResult | null; onClose: () => void }) {
  const [copied, setCopied] = useState(false)
  const [exportingPdf, setExportingPdf] = useState(false)

  const handleCopy = async () => {
    if (!item) return
    await navigator.clipboard.writeText(item.text)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 1800)
  }

  return (
    <Modal open={!!item} onOpenChange={(open) => !open && onClose()} title={item?.fileName} className="max-w-lg" description={item ? formatDateTime(item.createdAt) : undefined}>
      {item && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-slate-100 dark:bg-white/[0.06]">
              {item.thumbnail ? (
                <img src={item.thumbnail} alt="" className="h-full w-full object-cover" />
              ) : (
                <FileImage className="h-5 w-5 text-slate-400" />
              )}
            </div>
            <div className="flex-1">
              <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                <span>Confidence</span>
                <span className="font-semibold text-emerald-500">{(item.confidence * 100).toFixed(2)}%</span>
              </div>
              <Progress value={item.confidence * 100} size="sm" />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <ModelBadge model={item.model} />
          </div>

          <div className="max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-3.5 dark:border-white/10 dark:bg-white/[0.02]">
            <p className="font-devanagari whitespace-pre-wrap text-sm leading-relaxed text-slate-800 dark:text-slate-100">{item.text}</p>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            <Button variant="secondary" size="sm" onClick={handleCopy}>
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />} Copy
            </Button>
            <Button variant="secondary" size="sm" onClick={() => downloadTextFile(item.text, `${item.fileName}.txt`)}>
              <Download className="h-3.5 w-3.5" /> TXT
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={exportingPdf}
              onClick={async () => {
                setExportingPdf(true)
                try {
                  await downloadTextAsPdf(item.text, `${item.fileName}.pdf`)
                } finally {
                  setExportingPdf(false)
                }
              }}
            >
              <FileDown className="h-3.5 w-3.5" /> PDF
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
