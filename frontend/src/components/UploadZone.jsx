import { useDropzone } from 'react-dropzone'

const ACCEPT = {
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/bmp': ['.bmp'],
  'image/tiff': ['.tiff'],
  'application/pdf': ['.pdf'],
}
const MAX_SIZE = 10 * 1024 * 1024 // 10 MB

export default function UploadZone({ onFile, disabled }) {
  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop: files => files[0] && onFile(files[0]),
    accept: ACCEPT,
    maxSize: MAX_SIZE,
    multiple: false,
    disabled,
  })

  const rejection = fileRejections[0]?.errors[0]

  return (
    <div>
      <div
        {...getRootProps()}
        className={[
          'dropzone',
          isDragActive ? 'dropzone--active' : '',
          disabled ? 'dropzone--disabled' : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        <input {...getInputProps()} />
        <div className="dropzone__icon">📄</div>
        <p className="dropzone__text">
          {isDragActive ? 'Drop the file here…' : 'Drag & drop an image or PDF'}
        </p>
        <p className="dropzone__hint">PNG, JPG, BMP, TIFF, PDF — max 10 MB</p>
        <button type="button" className="btn btn--outline" disabled={disabled}>
          Browse files
        </button>
      </div>
      {rejection && (
        <p className="field-error">
          {rejection.code === 'file-too-large'
            ? 'File exceeds the 10 MB limit.'
            : 'Unsupported file type. Use PNG, JPG, BMP, TIFF, or PDF.'}
        </p>
      )}
    </div>
  )
}
