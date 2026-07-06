import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Maximize2, RotateCw, X, ZoomIn, ZoomOut } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { formatBytes } from '@/lib/utils'
import { ScanningOverlay } from '@/features/ocr/ScanningOverlay'

export interface FilePreviewProps {
  file: File
  onClear: () => void
  isProcessing?: boolean
  disabled?: boolean
}

export function FilePreview({ file, onClear, isProcessing, disabled }: FilePreviewProps) {
  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [url, setUrl] = useState<string | null>(null)

  useEffect(() => {
    if (isPdf) {
      setUrl(null)
      return
    }
    const objectUrl = URL.createObjectURL(file)
    setUrl(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [file, isPdf])

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-white/10 dark:bg-white/[0.02]">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2.5 dark:border-white/10">
        <p className="truncate text-sm font-medium text-slate-700 dark:text-slate-200">Preview</p>
        <button
          onClick={onClear}
          disabled={disabled}
          aria-label="Remove file"
          className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-rose-500 disabled:pointer-events-none disabled:opacity-40 dark:hover:bg-white/[0.06]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="relative flex min-h-[16rem] flex-1 items-center justify-center overflow-hidden bg-slate-50 p-4 dark:bg-black/20">
        {isPdf ? (
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-50 text-rose-500 dark:bg-rose-500/10">
              <FileText className="h-7 w-7" />
            </div>
            <div>
              <p className="max-w-[14rem] truncate text-sm font-medium text-slate-700 dark:text-slate-200">{file.name}</p>
              <p className="text-xs text-slate-400">{formatBytes(file.size)} · PDF · first page will be used</p>
            </div>
          </div>
        ) : (
          <motion.img
            src={url ?? undefined}
            alt="Uploaded handwriting preview"
            className="max-h-72 rounded-lg object-contain shadow-soft"
            animate={{ scale: zoom, rotate: rotation }}
            transition={{ type: 'spring', stiffness: 200, damping: 22 }}
          />
        )}

        {isProcessing && <ScanningOverlay />}
      </div>

      {!isPdf && (
        <div className="flex items-center justify-center gap-1 border-t border-slate-200 px-4 py-2 dark:border-white/10">
          <Button variant="ghost" size="icon" onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))} aria-label="Zoom out">
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setZoom((z) => Math.min(2.5, z + 0.25))} aria-label="Zoom in">
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setRotation((r) => r + 90)} aria-label="Rotate">
            <RotateCw className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              setZoom(1)
              setRotation(0)
            }}
            aria-label="Reset view"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
