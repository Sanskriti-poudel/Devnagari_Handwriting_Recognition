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

  const conf = result.confidence != null ? result.confidence * 100 : null

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

      {result.preprocessed_b64 && (
        <div className="result__preprocessed">
          <span className="result__preprocessed-label">What the model sees (64×64):</span>
          <img
            src={result.preprocessed_b64}
            alt="Preprocessed input"
            className="result__preprocessed-img"
          />
        </div>
      )}

      <div className="result__meta">
        <span className="badge">
          Model: <strong>{result.model_used}</strong>
        </span>
        {conf !== null && (
          <div className="confidence-wrapper">
            <span className="badge confidence-label">Confidence:</span>
            <div className="confidence-bar" title={`${conf.toFixed(1)}%`}>
              <div
                className="confidence-bar__fill"
                style={{ width: `${conf.toFixed(1)}%` }}
              />
            </div>
            <span className="confidence-value">{conf.toFixed(1)}%</span>
          </div>
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
