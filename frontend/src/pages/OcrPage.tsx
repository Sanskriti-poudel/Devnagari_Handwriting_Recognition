import { useState } from 'react'
import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { Alert } from '@/components/ui/Alert'
import { PageTransition } from '@/components/common/PageTransition'
import { UploadArea } from '@/features/ocr/UploadArea'
import { FilePreview } from '@/features/ocr/FilePreview'
import { ModelSelector } from '@/features/ocr/ModelSelector'
import { ResultPanel, ResultPlaceholder } from '@/features/ocr/ResultPanel'
import { RecentOcrStrip } from '@/features/ocr/RecentOcrStrip'
import { DocumentResultPanel } from '@/features/documents/DocumentResultPanel'
import { TextTools } from '@/features/documents/TextTools'
import { useModels } from '@/hooks/useModels'
import { useRecognize, useRecognizeDocument } from '@/hooks/useOcr'
import { useSettingsStore } from '@/stores/settings.store'
import type { DocumentOcrResponse, OcrModelId, OcrResult } from '@/types'

function isPdfFile(file: File) {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
}

export default function OcrPage() {
  const { data: models } = useModels()
  const defaultModel = useSettingsStore((s) => s.defaultModel)
  const [file, setFile] = useState<File | null>(null)
  const [model, setModel] = useState<OcrModelId>(defaultModel)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [result, setResult] = useState<OcrResult | null>(null)
  const [docResult, setDocResult] = useState<DocumentOcrResponse | null>(null)
  const [docText, setDocText] = useState('')

  const { mutate, isPending, error, reset } = useRecognize(setUploadProgress)
  const { mutate: mutateDoc, isPending: isDocPending, error: docError, reset: resetDoc } = useRecognizeDocument()

  const handleFileSelect = (selected: File) => {
    setFile(selected)
    setResult(null)
    setDocResult(null)
    reset()
    resetDoc()
  }

  const handleClear = () => {
    setFile(null)
    setResult(null)
    setDocResult(null)
    setDocText('')
    setUploadProgress(0)
    reset()
    resetDoc()
  }

  const handleRecognize = () => {
    if (!file) return
    if (isPdfFile(file)) {
      mutateDoc(
        { file, model },
        { onSuccess: (data) => { setDocResult(data); setDocText(data.text) } }
      )
      return
    }
    setUploadProgress(0)
    mutate(
      { file, model },
      {
        onSuccess: (data) => setResult(data),
      }
    )
  }

  const isBusy = isPending || isDocPending
  const activeError = error || docError

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <Breadcrumb items={[{ label: 'OCR' }]} />
          <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">Recognize Handwriting</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Upload a handwritten Devanagari image or PDF and let the AI convert it to Unicode text.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="space-y-4 lg:col-span-2">
            {file ? (
              <FilePreview file={file} onClear={handleClear} isProcessing={isBusy} disabled={isBusy} />
            ) : (
              <UploadArea onFileSelect={handleFileSelect} disabled={isBusy} />
            )}

            {file && (
              <Card>
                {models && <ModelSelector models={models} value={model} onChange={setModel} disabled={isBusy} />}
              </Card>
            )}

            {isBusy && (
              <Card>
                <div className="mb-1.5 flex items-center justify-between text-xs font-medium text-slate-500">
                  <span>Uploading &amp; recognizing…</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress || 8} />
              </Card>
            )}

            {activeError && <Alert variant="error" title="Recognition failed">{activeError.message}</Alert>}

            {file && (
              <Button size="lg" className="w-full" onClick={handleRecognize} loading={isBusy} disabled={isBusy}>
                <motion.span
                  animate={isBusy ? {} : { rotate: [0, 15, -15, 0] }}
                  transition={{ duration: 1.6, repeat: Infinity, repeatDelay: 1 }}
                  className="inline-flex"
                >
                  <Sparkles className="h-4 w-4" />
                </motion.span>
                {isBusy ? 'Recognizing…' : 'Recognize Text'}
              </Button>
            )}
          </div>

          <div className="lg:col-span-3">
            {docResult ? (
              <DocumentResultPanel result={docResult} text={docText} onTextChange={setDocText} />
            ) : result ? (
              <ResultPanel result={result} onClear={handleClear} />
            ) : (
              <ResultPlaceholder />
            )}
          </div>
        </div>

        <RecentOcrStrip />

        <TextTools />
      </div>
    </PageTransition>
  )
}
