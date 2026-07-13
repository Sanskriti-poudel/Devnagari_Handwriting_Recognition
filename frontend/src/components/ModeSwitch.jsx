export default function ModeSwitch({ mode, onChange, disabled }) {
  return (
    <div className="mode-switch">
      <button
        type="button"
        className={['mode-switch__tab', mode === 'char' ? 'is-active' : ''].filter(Boolean).join(' ')}
        onClick={() => onChange('char')}
        disabled={disabled}
      >
        Single character
      </button>
      <button
        type="button"
        className={['mode-switch__tab', mode === 'document' ? 'is-active' : ''].filter(Boolean).join(' ')}
        onClick={() => onChange('document')}
        disabled={disabled}
      >
        Document → text
      </button>
    </div>
  )
}
