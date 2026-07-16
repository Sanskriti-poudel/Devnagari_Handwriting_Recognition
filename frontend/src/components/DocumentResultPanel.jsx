import { useState } from 'react'
import toast from 'react-hot-toast'
import { exportDocument } from '../api/client'
import { romanToDevanagari } from '../lib/translit'

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export default function DocumentResultPanel({ result, docId, text, onTextChange }) {
  const [romanOn, setRomanOn] = useState(false)
  const [exporting, setExporting] = useState(null)
  const [pageIdx, setPageIdx] = useState(0)

  if (!result) return null

  const pages = result.pages || []
  const multiPage = pages.length > 1
  const currentPage = pages[pageIdx] || {}

  const engineLabel = result.engine === 'word-trocr' ? 'Word-level TrOCR' : 'CRNN (char)'

  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  const handleKeyDown = (e) => {
    if (!romanOn || (e.key !== ' ' && e.key !== 'Enter')) return
    const el = e.target
    if (el.selectionStart !== el.selectionEnd) return
    const pos = el.selectionStart
    const m = el.value.slice(0, pos).match(/([A-Za-z]+)$/)
    if (!m) return
    const token = m[1]
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

  const handleExport = async (format) => {
    if (!text.trim() && format !== 'pdf') {
      toast.error('Nothing to export yet — run a document scan first.')
      return
    }
    if (format === 'pdf' && !docId) {
      toast.error('Searchable PDF needs the original scan — re-run the document, then export.')
      return
    }
    setExporting(format)
    try {
      const blob = await exportDocument(format, text, docId)
      downloadBlob(blob, `recognized.${format}`)
    } catch (err) {
      const raw = err.response?.data?.detail ?? err.response?.data?.error ?? err.message ?? 'Export failed'
      toast.error(typeof raw === 'string' ? raw : JSON.stringify(raw))
    } finally {
      setExporting(null)
    }
  }

  const pct = Math.round((result.avg_confidence || 0) * 100)

  return (
    <div className="doc-result">
      {result.annotated && !multiPage && (
        <img className="doc-result__annotated" src={result.annotated} alt="Annotated scan" />
      )}

      {multiPage && (
        <div className="doc-result__page-viewer">
          <div className="doc-result__page-nav">
            {pages.map((_, i) => (
              <button
                key={i}
                type="button"
                className={['page-dot', i === pageIdx ? 'page-dot--active' : ''].filter(Boolean).join(' ')}
                onClick={() => setPageIdx(i)}
                aria-label={`Page ${i + 1}`}
              />
            ))}
          </div>
          {pages[pageIdx]?.annotated && (
            <img
              className="doc-result__annotated"
              src={pages[pageIdx].annotated}
              alt={`Page ${pageIdx + 1} annotated`}
            />
          )}
          <div className="doc-result__page-info">
            Page {pageIdx + 1} of {pages.length} · {pages[pageIdx]?.num_lines || 0} lines · {pages[pageIdx]?.num_chars || 0} chars ·{' '}
            {Math.round((pages[pageIdx]?.avg_confidence || 0) * 100)}% conf
          </div>
        </div>
      )}

      <div className="doc-result__stats">
        {engineLabel} · {result.num_lines} line(s) · {result.num_chars} chars · avg conf {pct}% ·{' '}
        {result.time_ms} ms
      </div>

      <label className="doc-result__toggle">
        <input type="checkbox" checked={romanOn} onChange={e => setRomanOn(e.target.checked)} />
        Romanized typing (type "namaste" → नमस्ते, press space/enter)
      </label>

      <textarea
        className="result__textarea doc-result__textarea"
        value={text}
        onChange={e => onTextChange(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={10}
        lang="ne"
        spellCheck={false}
      />

      <div className="result__actions">
        <button type="button" className="btn btn--outline btn--sm" onClick={handleCopy}>
          Copy text
        </button>
        <button
          type="button"
          className="btn btn--outline btn--sm"
          onClick={() => handleExport('txt')}
          disabled={exporting !== null}
        >
          {exporting === 'txt' ? '…' : 'Download .txt'}
        </button>
        <button
          type="button"
          className="btn btn--outline btn--sm"
          onClick={() => handleExport('docx')}
          disabled={exporting !== null}
        >
          {exporting === 'docx' ? '…' : 'Download .docx'}
        </button>
        <button
          type="button"
          className="btn btn--primary btn--sm"
          onClick={() => handleExport('pdf')}
          disabled={exporting !== null}
        >
          {exporting === 'pdf' ? '…' : 'Searchable PDF'}
        </button>
      </div>
    </div>
  )
}
