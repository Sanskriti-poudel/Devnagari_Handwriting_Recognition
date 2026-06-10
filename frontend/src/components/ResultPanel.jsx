import toast from 'react-hot-toast'

export default function ResultPanel({ result }) {
  if (!result) return null

  const handleCopy = () => {
    navigator.clipboard.writeText(result.recognized_text)
    toast.success('Copied to clipboard')
  }

  const handleDownload = () => {
    const blob = new Blob([result.recognized_text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.filename.replace(/\.[^.]+$/, '') + '_ocr.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="result">
      <div className="result__header">
        <h3 className="result__title">Recognized Text</h3>
        <div className="result__actions">
          <button type="button" className="btn btn--outline btn--sm" onClick={handleCopy}>
            Copy
          </button>
          <button type="button" className="btn btn--primary btn--sm" onClick={handleDownload}>
            Download .txt
          </button>
        </div>
      </div>

      <textarea
        className="result__textarea"
        value={result.recognized_text}
        readOnly
        rows={6}
        lang="ne"
        spellCheck={false}
      />

      <div className="result__meta">
        <span className="badge">
          Model: <strong>{result.model_used}</strong>
        </span>
        {result.confidence != null && (
          <span className="badge">
            Confidence: <strong>{(result.confidence * 100).toFixed(1)}%</strong>
          </span>
        )}
        {result.processing_time_ms != null && (
          <span className="badge">
            Time: <strong>{result.processing_time_ms.toFixed(0)} ms</strong>
          </span>
        )}
        {result.id != null && (
          <span className="badge badge--muted">ID: {result.id}</span>
        )}
      </div>
    </div>
  )
}
