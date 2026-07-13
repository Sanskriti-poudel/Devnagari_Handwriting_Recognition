import { useState } from 'react'
import toast from 'react-hot-toast'
import { preetiToUnicode, unicodeToPreeti } from '../lib/preeti'

export default function TextTools() {
  const [dir, setDir] = useState('p2u') // 'p2u' | 'u2p'
  const [input, setInput] = useState('')

  const isP2U = dir === 'p2u'
  const output = input ? (isP2U ? preetiToUnicode(input) : unicodeToPreeti(input)) : ''

  const handleCopy = () => {
    navigator.clipboard.writeText(output)
    toast.success('Copied to clipboard')
  }

  const handleSwap = () => {
    setInput(output)
    setDir(isP2U ? 'u2p' : 'p2u')
  }

  return (
    <div className="text-tools">
      <h3 className="result__title">Nepali text tools — Preeti ↔ Unicode</h3>

      <div className="mode-switch">
        <button
          type="button"
          className={['mode-switch__tab', isP2U ? 'is-active' : ''].filter(Boolean).join(' ')}
          onClick={() => setDir('p2u')}
        >
          Preeti → Unicode
        </button>
        <button
          type="button"
          className={['mode-switch__tab', !isP2U ? 'is-active' : ''].filter(Boolean).join(' ')}
          onClick={() => setDir('u2p')}
        >
          Unicode → Preeti
        </button>
      </div>

      <div className="text-tools__row">
        <div className="text-tools__col">
          <label className="text-tools__label">
            {isP2U ? 'Preeti text (paste here)' : 'Unicode text (paste here)'}
          </label>
          <textarea
            className={['result__textarea', isP2U ? 'text-tools__mono' : ''].filter(Boolean).join(' ')}
            value={input}
            onChange={e => setInput(e.target.value)}
            rows={4}
            placeholder={isP2U ? 'Paste Preeti-encoded text, e.g.  g]kfn' : 'नेपाली युनिकोड यहाँ पेस्ट गर्नुहोस्'}
          />
        </div>
        <div className="text-tools__col">
          <label className="text-tools__label">{isP2U ? 'Unicode' : 'Preeti'}</label>
          <textarea
            className={['result__textarea', !isP2U ? 'text-tools__mono' : ''].filter(Boolean).join(' ')}
            value={output}
            readOnly
            rows={4}
          />
        </div>
      </div>

      <div className="result__actions">
        <button type="button" className="btn btn--outline btn--sm" onClick={handleCopy}>
          Copy
        </button>
        <button type="button" className="btn btn--outline btn--sm" onClick={handleSwap}>
          Swap as input
        </button>
      </div>
    </div>
  )
}
