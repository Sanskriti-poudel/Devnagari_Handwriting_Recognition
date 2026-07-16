import { useState, type KeyboardEvent } from 'react'
import { motion } from 'framer-motion'
import { Copy, Download } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Textarea } from '@/components/ui/Textarea'
import { Switch } from '@/components/ui/Switch'
import { toast } from '@/components/ui/Toast'
import { romanToDevanagari } from '@/lib/translit'
import { documentService } from '@/services/document.service'
import type { DocumentOcrResponse, ExportFormat } from '@/types'

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

interface DocumentResultPanelProps {
  result: DocumentOcrResponse
  text: string
  onTextChange: (text: string) => void
}

export function DocumentResultPanel({ result, text, onTextChange }: DocumentResultPanelProps) {
  const [romanOn, setRomanOn] = useState(false)
  const [exporting, setExporting] = useState<ExportFormat | null>(null)

  const engineLabel = result.engine === 'word-trocr' ? 'Word-level TrOCR' : 'CRNN (char)'
  const pct = Math.round((result.avgConfidence || 0) * 100)

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (!romanOn || (e.key !== ' ' && e.key !== 'Enter')) return
    const el = e.currentTarget
    if (el.selectionStart !== el.selectionEnd) return
    const pos = el.selectionStart
    const match = el.value.slice(0, pos).match(/([A-Za-z]+)$/)
    if (!match) return
    const token = match[1]
    const dev = romanToDevanagari(token)
    if (dev === token) return
    e.preventDefault()
    const sep = e.key === 'Enter' ? '\n' : ' '
    const start = pos - token.length
    const next = el.value.slice(0, start) + dev + sep + el.value.slice(pos)
    onTextChange(next)
    requestAnimationFrame(() => {
      const caret = start + dev.length + sep.length
      el.selectionStart = el.selectionEnd = caret
    })
  }

  const handleExport = async (format: ExportFormat) => {
    if (!text.trim() && format !== 'pdf') {
      toast.error('Nothing to export yet — run a document scan first.')
      return
    }
    if (format === 'pdf' && !result.docId) {
      toast.error('Searchable PDF needs the original scan — re-run the document, then export.')
      return
    }
    setExporting(format)
    try {
      // For DOCX: flatten all page lines to preserve layout
      const lineData = format === 'docx' && result.pages
        ? result.pages.flatMap(p => p.lines || [])
        : undefined
      const blob = await documentService.exportDocument(format, text, result.docId, lineData)
      downloadBlob(blob, `recognized.${format}`)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExporting(null)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <Card>
        <CardHeader>
          <CardTitle>Document Recognition Result</CardTitle>
          <Badge variant="violet">{engineLabel}</Badge>
        </CardHeader>

        {result.annotated && (
          <img
            src={result.annotated}
            alt="Annotated scan"
            className="mb-4 max-h-64 w-full rounded-xl border border-slate-200 object-contain dark:border-white/10"
          />
        )}

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Badge variant="outline">{result.numPages} page(s)</Badge>
          <Badge variant="outline">{result.numLines} line(s)</Badge>
          <Badge variant="outline">{result.numChars} chars</Badge>
          <Badge variant="outline">avg conf {pct}%</Badge>
          <Badge variant="outline">{result.timeMs} ms</Badge>
        </div>

        <label className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-500 dark:text-slate-400">
          <Switch checked={romanOn} onCheckedChange={setRomanOn} />
          Romanized typing (type "namaste" → नमस्ते, press space/enter)
        </label>

        <Textarea
          className="font-devanagari"
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={10}
          lang="ne"
          spellCheck={false}
        />

        <div className="mt-4 grid grid-cols-4 gap-2.5">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-3.5 w-3.5" /> Copy
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport('txt')} loading={exporting === 'txt'} disabled={exporting !== null}>
            <Download className="h-3.5 w-3.5" /> .txt
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport('docx')} loading={exporting === 'docx'} disabled={exporting !== null}>
            <Download className="h-3.5 w-3.5" /> .docx
          </Button>
          <Button variant="primary" size="sm" onClick={() => handleExport('pdf')} loading={exporting === 'pdf'} disabled={exporting !== null}>
            <Download className="h-3.5 w-3.5" /> Searchable PDF
          </Button>
        </div>
      </Card>
    </motion.div>
  )
}
