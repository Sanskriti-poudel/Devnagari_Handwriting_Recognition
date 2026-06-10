import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { fetchModels, runOCR } from './api/client'
import UploadZone from './components/UploadZone'
import ImagePreview from './components/ImagePreview'
import ResultPanel from './components/ResultPanel'
import ModelSelector from './components/ModelSelector'
import './App.css'

export default function App() {
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('crnn')
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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
    setError(null)
    setPreviewUrl(f.type !== 'application/pdf' ? URL.createObjectURL(f) : null)
  }, [])

  const handleRecognize = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await runOCR(file, selectedModel)
      setResult(data)
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
          <ModelSelector
            models={models}
            value={selectedModel}
            onChange={setSelectedModel}
            disabled={loading}
          />
        </div>

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
                  Processing…
                </>
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

        {result && (
          <div className="card">
            <ResultPanel result={result} />
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Devanagari Handwritten Document Recognition — United Technical College, 2026</p>
      </footer>
    </div>
  )
}
