import { useState, useRef } from 'react'

export default function BrandUpload() {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  const fileRef = useRef(null)

  const handleUpload = async (file) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.')
      return
    }

    setUploading(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch('/api/brands/upload', {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setError(`Upload failed: ${e.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div>
      <h2 className="section-title">📄 Brand Documents</h2>

      <div
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0])}
        />
        <div className="upload-icon">📄</div>
        <div className="upload-text">
          {uploading ? 'Uploading & Processing...' : 'Drop your Brand Strategy PDF here'}
        </div>
        <div className="upload-hint">
          or click to browse · PDF files only · Brand Strategy, Marketing Plans, etc.
        </div>
      </div>

      {error && (
        <div style={{
          marginTop: 'var(--space-md)',
          padding: 'var(--space-md)',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 'var(--border-radius)',
          color: '#ef4444',
          fontSize: '0.9rem',
        }}>
          ⚠️ {error}
        </div>
      )}

      {uploading && (
        <div className="loading">
          <div className="spinner" />
          <span>Processing PDF and embedding into knowledge base...</span>
        </div>
      )}

      {result && (
        <div style={{
          marginTop: 'var(--space-lg)',
          padding: 'var(--space-lg)',
          background: 'var(--bg-card)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: 'var(--border-radius)',
        }}>
          <h3 style={{ color: 'var(--accent-success)', marginBottom: 'var(--space-md)', fontSize: '1rem' }}>
            ✅ Brand Document Processed
          </h3>
          <div className="stats-bar">
            <div className="stat">
              <span className="stat-value">{result.pages_processed}</span>
              <span className="stat-label">Pages</span>
            </div>
            <div className="stat">
              <span className="stat-value">{result.chunks_stored}</span>
              <span className="stat-label">Chunks Stored</span>
            </div>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            File: {result.filename} — Brand context is now available for angle generation.
          </p>
        </div>
      )}
    </div>
  )
}
