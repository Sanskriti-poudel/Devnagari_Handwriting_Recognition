export default function ModelSelector({ models, value, onChange, disabled }) {
  return (
    <div className="model-selector">
      <label htmlFor="model-select" className="model-selector__label">
        OCR Model
      </label>
      <select
        id="model-select"
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        className="select"
      >
        {models.length > 0
          ? models.map(m => (
              <option key={m.name} value={m.name} disabled={!m.available}>
                {m.name === 'crnn' ? 'CRNN (CNN–RNN–CTC baseline)' : 'Transformer (TrOCR)'}
                {!m.available ? ' — not loaded' : ''}
              </option>
            ))
          : [
              <option key="crnn" value="crnn">CRNN (CNN–RNN–CTC baseline)</option>,
              <option key="transformer" value="transformer">Transformer (TrOCR)</option>,
            ]}
      </select>
    </div>
  )
}
