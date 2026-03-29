import { useState, useCallback } from 'react';
import AngleCard from '../components/AngleCard';
import { generateAngles } from '../api';

export default function AnglesPage() {
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mock, setMock] = useState(false);
  const [maxTrends, setMaxTrends] = useState(8);
  const [anglesPerTrend, setAnglesPerTrend] = useState(3);
  const [provider, setProvider] = useState('gemini');

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await generateAngles(mock, maxTrends, anglesPerTrend, '', provider);
      setOutput(data);
    } catch (e) {
      setError(`Failed to generate angles: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [mock, maxTrends, anglesPerTrend, provider]);

  return (
    <div className="angles-page fade-in">
      <header className="page-header">
        <h1 className="page-title">Content Angles</h1>
        <p className="page-subtitle">AI-powered content generation with psychological triggers</p>
      </header>

      <div className="controls-bar card">
        <div className="control-group">
          <label>Provider</label>
          <select value={provider} onChange={(e) => setProvider(e.target.value)} disabled={loading}>
            <option value="gemini">Google Gemini</option>
            <option value="claude">Anthropic Claude</option>
            <option value="lmstudio">LM Studio (Local)</option>
          </select>
        </div>

        <div className="control-group">
          <label>Trends</label>
          <input
            type="number"
            value={maxTrends}
            onChange={(e) => setMaxTrends(Number(e.target.value))}
            min={1}
            max={20}
            disabled={loading}
          />
        </div>

        <div className="control-group">
          <label>Angles / Trend</label>
          <input
            type="number"
            value={anglesPerTrend}
            onChange={(e) => setAnglesPerTrend(Number(e.target.value))}
            min={1}
            max={5}
            disabled={loading}
          />
        </div>

        <div className="control-group">
          <label>Mode</label>
          <div className="toggle-switch">
            <span className={!mock ? 'active' : ''}>LIVE</span>
            <input
              type="checkbox"
              checked={mock}
              onChange={(e) => setMock(e.target.checked)}
              disabled={loading}
            />
            <span className={mock ? 'active' : ''}>MOCK</span>
          </div>
        </div>

        <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <span className="spinner-container">
              <span className="spinner spinner-white" /> Generating...
            </span>
          ) : (
            '⚡ Generate Now'
          )}
        </button>
      </div>

      {error && (
        <div className="error-card card">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{error}</span>
        </div>
      )}

      {loading && !output && (
        <div className="skeleton-angles">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="skeleton-angle-card shimmer" />
          ))}
        </div>
      )}

      {output && (
        <div className="angles-results fade-in">
          <div className="stats-bar card">
            <div className="stat">
              <span className="stat-value">{output.trend_count}</span>
              <span className="stat-label">Trends Scanned</span>
            </div>
            <div className="stat">
              <span className="stat-value">{output.angle_count}</span>
              <span className="stat-label">Angles Created</span>
            </div>
            <div className="stat">
              <span className="stat-value">{output.provider_used}</span>
              <span className="stat-label">AI Engine</span>
            </div>
          </div>

          <div className="trends-with-angles">
            {output.results?.map((result, i) => (
              <section key={i} className="trend-with-angles-group">
                <div className="trend-summary-header card">
                  <div className="trend-header-main">
                    <h2 className="trend-title-sm">{result.trend.title}</h2>
                    <span className="trend-source-meta">{result.trend.source_name || result.trend.source}</span>
                  </div>
                  <div className="trend-jack-wrap">
                    <span className="jack-label">Jack Potential</span>
                    <span className="jack-pct">{(result.trend.jack_potential * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div className="angles-grid">
                  {result.angles?.map((angle, j) => (
                    <AngleCard key={j} angle={angle} trend={result.trend} filenameStem={`${result.trend.title.replace(/\s+/g, '-').toLowerCase()}-${j}`} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>
      )}

      {!loading && !output && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">✍️</div>
          <h3>Ready to generate?</h3>
          <p>Discover trends and turn them into viral content angles with just one click.</p>
        </div>
      )}
    </div>
  );
}
