export default function ImagePreview({ file, previewUrl }) {
  if (!file) return null

  const isPdf = file.type === 'application/pdf'

  return (
    <div className="preview">
      <p className="preview__filename" title={file.name}>
        {file.name}
      </p>
      {isPdf ? (
        <div className="preview__pdf">
          <span className="preview__pdf-icon">📑</span>
          <span className="preview__pdf-label">
            PDF &mdash; {(file.size / 1024).toFixed(1)} KB
          </span>
        </div>
      ) : (
        <img src={previewUrl} alt={`Preview of ${file.name}`} className="preview__img" />
      )}
    </div>
  )
}
