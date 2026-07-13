import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { fetchModels, runOCR, runDocumentOCR } from './api/client'
import UploadZone from './components/UploadZone'
import ImagePreview from './components/ImagePreview'
import ResultPanel from './components/ResultPanel'
import ModelSelector from './components/ModelSelector'
import ModeSwitch from './components/ModeSwitch'
import DocumentResultPanel from './components/DocumentResultPanel'
import TextTools from './components/TextTools'
import './App.css'

export default function App() {
  const [mode, setMode] = useState('char') // 'char' | 'document'
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('crnn')
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [docResult, setDocResult] = useState(null)
  const [docId, setDocId] = useState(null)
  const [docText, setDocText] = useState('')

  useEffect(() => {
    fetchModels()
      .then(setModels)
      .catch(() => {}) // backend may not be running yet — use defaults
  }, [])

  // Clean up object URL when it changes
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  const handleFile = useCallback(f => {
    setFile(f)
    setResult(null)
    setDocResult(null)
    setDocId(null)
    setDocText('')
    setError(null)
    setPreviewUrl(f.type !== 'application/pdf' ? URL.createObjectURL(f) : null)
  }, [])

  const handleModeChange = useCallback(next => {
    setMode(next)
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
    setDocResult(null)
    setDocId(null)
    setDocText('')
    setError(null)
  }, [])

  const handleRecognize = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    setDocResult(null)
    try {
      if (mode === 'document') {
        const data = await runDocumentOCR(file)
        setDocResult(data)
        setDocId(data.doc_id)
        setDocText(data.text || '')
      } else {
        const data = await runOCR(file, selectedModel)
        setResult(data)
      }
    } catch (err) {
      const raw = err.response?.data?.detail ?? err.response?.data?.error ?? err.message ?? 'OCR failed'
      const msg = typeof raw === 'string' ? raw : JSON.stringify(raw)
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1 className="header__title">Devanagari OCR</h1>
        <p className="header__subtitle">देवनागरी हस्तलेख पहिचान</p>
      </header>

      <main className="main">
        <div className="card">
          <ModeSwitch mode={mode} onChange={handleModeChange} disabled={loading} />
        </div>

        {mode === 'char' && (
          <div className="card">
            <ModelSelector
              models={models}
              value={selectedModel}
              onChange={setSelectedModel}
              disabled={loading}
            />
          </div>
        )}

        <div className="card upload-row">
          <div className="upload-row__zone">
            <UploadZone onFile={handleFile} disabled={loading} />
          </div>
          {file && (
            <div className="upload-row__preview">
              <ImagePreview file={file} previewUrl={previewUrl} />
            </div>
          )}
        </div>

        {file && (
          <div className="recognize-bar">
            <button
              type="button"
              className="btn btn--primary btn--lg"
              onClick={handleRecognize}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  {mode === 'document' ? 'Reading document…' : 'Processing…'}
                </>
              ) : mode === 'document' ? (
                'Read Document'
              ) : (
                'Recognize Text'
              )}
            </button>
          </div>
        )}

        {error && !loading && (
          <div className="alert alert--error" role="alert">
            {error}
          </div>
        )}

        {mode === 'char' && result && (
          <div className="card">
            <ResultPanel result={result} />
          </div>
        )}

        {mode === 'document' && docResult && (
          <div className="card">
            <DocumentResultPanel
              result={docResult}
              docId={docId}
              text={docText}
              onTextChange={setDocText}
            />
          </div>
        )}

        <div className="card">
          <TextTools />
        </div>
      </main>

      <footer className="footer">
        <p>Devanagari Handwritten Document Recognition — United Technical College, 2026</p>
      </footer>
    </div>
  )
}
