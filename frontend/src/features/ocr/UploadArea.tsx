import { useCallback, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, UploadCloud } from 'lucide-react'
import { cn } from '@/lib/utils'
import { toast } from '@/components/ui/Toast'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
const ACCEPTED_EXT = ['.jpg', '.jpeg', '.png', '.pdf']
const MAX_SIZE_BYTES = 20 * 1024 * 1024

export interface UploadAreaProps {
  onFileSelect: (file: File) => void
  disabled?: boolean
}

function isValidFile(file: File): string | null {
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!ACCEPTED_TYPES.includes(file.type) && !ACCEPTED_EXT.includes(ext)) {
    return 'Unsupported file type. Please upload a JPG, PNG, or PDF.'
  }
  if (file.size > MAX_SIZE_BYTES) {
    return 'File is too large. Maximum size is 20MB.'
  }
  return null
}

export function UploadArea({ onFileSelect, disabled }: UploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0]
      if (!file) return
      const error = isValidFile(file)
      if (error) {
        toast.error('Invalid file', error)
        return
      }
      onFileSelect(file)
    },
    [onFileSelect]
  )

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload a handwritten image or PDF"
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => e.key === 'Enter' && !disabled && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragging(false)
        if (!disabled) handleFiles(e.dataTransfer.files)
      }}
      className={cn(
        'relative flex min-h-[22rem] cursor-pointer flex-col items-center justify-center overflow-hidden rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300',
        isDragging
          ? 'scale-[1.01] border-violet-500 bg-violet-50/60 dark:bg-violet-500/10'
          : 'border-slate-300 bg-slate-50/50 hover:border-violet-400 hover:bg-violet-50/30 dark:border-white/15 dark:bg-white/[0.02] dark:hover:border-violet-500/50 dark:hover:bg-violet-500/[0.04]',
        disabled && 'pointer-events-none opacity-60'
      )}
    >
      {isDragging && (
        <motion.div
          layoutId="drag-ring"
          className="pointer-events-none absolute inset-3 rounded-xl border-2 border-violet-400"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.2, repeat: Infinity }}
        />
      )}

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXT.join(',')}
        className="sr-only"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <motion.div
        animate={{ y: isDragging ? [0, -10, 0] : [0, -6, 0] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
        className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-glow"
      >
        <UploadCloud className="h-7 w-7" />
      </motion.div>

      <p className="text-base font-semibold text-slate-800 dark:text-slate-100">Drag &amp; drop your file here</p>
      <p className="mt-1 text-sm font-medium text-violet-600 dark:text-violet-400">or click to browse</p>
      <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-400">
        <FileText className="h-3.5 w-3.5" /> Supports: JPG, PNG, PDF (Max 20MB)
      </p>
    </div>
  )
}
