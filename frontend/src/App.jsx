import { useState, useCallback } from 'react'
import Header from './components/Header'
import TrendDashboard from './components/TrendDashboard'
import AngleCard from './components/AngleCard'
import BrandUpload from './components/BrandUpload'

const API_BASE = '/api'

export default function App() {
  const [trends, setTrends] = useState([])
  const [output, setOutput] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingAction, setLoadingAction] = useState('')
  const [error, setError] = useState('')
  const [view, setView] = useState('dashboard') // dashboard | upload

  const scanTrends = useCallback(async (mock = false) => {
    setLoading(true)
    setLoadingAction('Scanning trends...')
    setError('')
    try {
      const res = await fetch(`${API_BASE}/trends?mock=${mock}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setTrends(data.trends || [])
    } catch (e) {
      setError(`Failed to scan trends: ${e.message}`)
    } finally {
      setLoading(false)
      setLoadingAction('')
    }
  }, [])

  const generateAngles = useCallback(async (mock = false) => {
    setLoading(true)
    setLoadingAction('Generating angles with psychological triggers...')
    setError('')
    try {
      const res = await fetch(`${API_BASE}/angles/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mock, max_trends: 8, angles_per_trend: 3 }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setOutput(data)
      setTrends([])
    } catch (e) {
      setError(`Failed to generate angles: ${e.message}`)
    } finally {
      setLoading(false)
      setLoadingAction('')
    }
  }, [])

  return (
    <div className="app-container">
      <Header />

      {/* Navigation */}
      <div className="controls">
        <button
          className={`btn ${view === 'dashboard' ? 'btn-primary' : ''}`}
          onClick={() => setView('dashboard')}
        >
          📊 Dashboard
        </button>
        <button
          className={`btn ${view === 'upload' ? 'btn-primary' : ''}`}
          onClick={() => setView('upload')}
        >
          📄 Upload Brand Docs
        </button>
        <div style={{ flex: 1 }} />
        <button
          className="btn"
          onClick={() => scanTrends(true)}
          disabled={loading}
        >
          🔍 Scan Trends (Mock)
        </button>
        <button
          className="btn"
          onClick={() => scanTrends(false)}
          disabled={loading}
        >
          🌐 Scan Trends (Live)
        </button>
        <button
          className="btn btn-primary"
          onClick={() => generateAngles(true)}
          disabled={loading}
        >
          🚀 Generate Angles (Mock)
        </button>
        <button
          className="btn btn-primary"
          onClick={() => generateAngles(false)}
          disabled={loading}
        >
          ⚡ Generate (Live AI)
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: 'var(--space-md)',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 'var(--border-radius)',
          color: '#ef4444',
          marginBottom: 'var(--space-lg)',
          fontSize: '0.9rem',
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading">
          <div className="spinner" />
          <span>{loadingAction}</span>
        </div>
      )}

      {/* Views */}
      {view === 'upload' && <BrandUpload />}

      {view === 'dashboard' && (
        <>
          {/* Stats Bar */}
          {output && (
            <div className="stats-bar">
              <div className="stat">
                <span className="stat-value">{output.trend_count}</span>
                <span className="stat-label">Trends</span>
              </div>
              <div className="stat">
                <span className="stat-value">{output.angle_count}</span>
                <span className="stat-label">Angles</span>
              </div>
              <div className="stat">
                <span className="stat-value">{output.provider_used}</span>
                <span className="stat-label">Provider</span>
              </div>
            </div>
          )}

          {/* Trends Grid (from scan) */}
          {trends.length > 0 && !output && (
            <TrendDashboard trends={trends} />
          )}

          {/* Full Results (from generate) */}
          {output && output.results && output.results.map((result, i) => (
            <div key={i} style={{ marginBottom: 'var(--space-2xl)' }}>
              {/* Trend Header */}
              <div className="trend-card" style={{ marginBottom: 'var(--space-md)' }}>
                <div className="trend-header">
                  <h3 className="trend-title">{result.trend.title}</h3>
                  {result.trend.jack_potential >= 0.85 && (
                    <span className="flash-badge">🔥 HOT</span>
                  )}
                </div>
                <p className="trend-description">{result.trend.description}</p>
                <div className="trend-meta">
                  <SourceBadge source={result.trend.source} />
                  <JackScore score={result.trend.jack_potential} />
                </div>
              </div>

              {/* Angles */}
              {result.angles.map((angle, j) => (
                <AngleCard key={j} angle={angle} index={j + 1} />
              ))}
            </div>
          ))}

          {/* Empty State */}
          {!loading && trends.length === 0 && !output && (
            <div className="empty-state">
              <div className="empty-state-icon">🎯</div>
              <p className="empty-state-text">
                Click <strong>Scan Trends</strong> to discover trending topics, or{' '}
                <strong>Generate Angles</strong> to run the full pipeline with psychological triggers.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function SourceBadge({ source }) {
  const config = {
    twitter_ksa: { cls: 'twitter', emoji: '🐦', label: 'Twitter/X KSA' },
    google_trends: { cls: 'google', emoji: '📈', label: 'Google Trends' },
    gulf_news: { cls: 'news', emoji: '📰', label: 'Gulf News' },
    cultural: { cls: 'cultural', emoji: '🎭', label: 'Cultural' },
  }
  const c = config[source] || config.gulf_news
  return <span className={`source-badge ${c.cls}`}>{c.emoji} {c.label}</span>
}

function JackScore({ score }) {
  const cls = score >= 0.8 ? 'high' : score >= 0.6 ? 'medium' : 'low'
  return <span className={`jack-score ${cls}`}>⚡ {(score * 100).toFixed(0)}%</span>
}
