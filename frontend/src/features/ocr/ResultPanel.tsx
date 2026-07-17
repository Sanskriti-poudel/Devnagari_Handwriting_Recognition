import { useState } from 'react'
import { motion } from 'framer-motion'
import { Check, Copy, Download, FileDown, RotateCcw, Sparkles } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Progress } from '@/components/ui/Progress'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { AnimatedNumber } from '@/components/common/AnimatedNumber'
import { ModelBadge } from '@/features/ocr/ModelBadge'
import { confidenceLabel } from '@/lib/utils'
import { downloadTextAsPdf, downloadTextFile } from '@/lib/export'
import { toast } from '@/components/ui/Toast'
import type { OcrResult } from '@/types'

export function ResultPanel({ result, onClear }: { result: OcrResult; onClear: () => void }) {
  const [copied, setCopied] = useState(false)
  const [exportingPdf, setExportingPdf] = useState(false)
  const { label, tone } = confidenceLabel(result.confidence)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.text)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 1800)
  }

  const handleDownloadTxt = () => {
    downloadTextFile(result.text, `${result.fileName.replace(/\.[^.]+$/, '')}.txt`)
  }

  const handleDownloadPdf = async () => {
    setExportingPdf(true)
    try {
      await downloadTextAsPdf(result.text, `${result.fileName.replace(/\.[^.]+$/, '')}.pdf`)
    } finally {
      setExportingPdf(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <Card>
        <CardHeader>
          <CardTitle>Recognition Result</CardTitle>
          <Badge variant={tone}>{label}</Badge>
        </CardHeader>

        <div className="mb-5">
          <div className="mb-1.5 flex items-end justify-between">
            <span className="text-xs font-medium text-slate-400">Confidence Score</span>
            <span className="text-2xl font-extrabold text-emerald-500">
              <AnimatedNumber value={result.confidence * 100} decimals={2} suffix="%" />
            </span>
          </div>
          <Progress value={result.confidence * 100} />
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <ModelBadge model={result.model} />
          {result.modelSimulated && (
            <Badge variant="amber">Simulated — backend model endpoint pending</Badge>
          )}
          {result.numChars != null && <Badge variant="outline">{result.numChars} characters</Badge>}
          {result.numLines != null && <Badge variant="outline">{result.numLines} lines</Badge>}
          {result.timeMs != null && <Badge variant="outline">{result.timeMs}ms</Badge>}
        </div>

        <div className="relative rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/[0.02]">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="absolute right-2.5 top-2.5"
            aria-label="Copy recognized text"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy'}
          </Button>
          <p className="font-devanagari max-h-56 overflow-y-auto whitespace-pre-wrap pr-16 text-base leading-loose text-slate-800 dark:text-slate-100">
            {result.text.split('\n').map((line, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.08 }}
                className="block"
              >
                {line || ' '}
              </motion.span>
            ))}
          </p>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-2.5">
          <Button variant="secondary" onClick={handleDownloadTxt}>
            <Download className="h-4 w-4" /> TXT
          </Button>
          <Button variant="primary" onClick={handleDownloadPdf} loading={exportingPdf}>
            <FileDown className="h-4 w-4" /> PDF
          </Button>
          <Button variant="outline" onClick={onClear}>
            <RotateCcw className="h-4 w-4" /> Clear
          </Button>
        </div>
      </Card>
    </motion.div>
  )
}

export function ResultPlaceholder() {
  return (
    <Card className="flex min-h-[20rem] flex-col items-center justify-center text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-brand-soft text-violet-500 dark:text-violet-400">
        <Sparkles className="h-6 w-6" />
      </div>
      <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">No recognition yet</p>
      <p className="mt-1 max-w-[16rem] text-xs text-slate-400">
        Upload a handwritten Devanagari image or PDF and click "Recognize Text" to see results here.
      </p>
    </Card>
  )
}
