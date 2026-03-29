import { useState, useCallback, useEffect } from 'react';
import TrendTable from '../components/TrendTable';
import { scanTrends, fetchSources } from '../api';

export default function DiscoveryPage() {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sources, setSources] = useState(['saudi_general']);
  const [selectedSource, setSelectedSource] = useState('saudi_general');
  const [mock, setMock] = useState(false);
  const [maxResults, setMaxResults] = useState(15);
  const [lastScan, setLastScan] = useState(null);

  useEffect(() => {
    fetchSources()
      .then(data => {
        const names = (data.sources || []).map(s => typeof s === 'string' ? s : s.name);
        setSources(names.length > 0 ? names : ['saudi_general']);
      })
      .catch(() => setSources(['saudi_general']));
  }, []);

  const handleScan = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await scanTrends(mock, maxResults, selectedSource);
      setTrends(data.trends || []);
      setLastScan(new Date());
    } catch (e) {
      setError(`Failed to scan trends: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [mock, maxResults, selectedSource]);

  return (
    <div className="discovery-page fade-in">
      <header className="page-header">
        <h1 className="page-title">Topic Discovery</h1>
        <p className="page-subtitle">
          {lastScan ? `Last scan: ${lastScan.toLocaleTimeString()}` : 'Real-time trend analysis and source discovery'}
        </p>
      </header>

      <div className="controls-bar card">
        <div className="control-group">
          <label htmlFor="source-select">Sources</label>
          <select
            id="source-select"
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            disabled={loading}
          >
            {sources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="max-results">Max Results</label>
          <input
            id="max-results"
            type="number"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            min={1}
            max={50}
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

        <button className="btn btn-primary" onClick={handleScan} disabled={loading}>
          {loading ? (
            <span className="spinner-container">
              <span className="spinner spinner-white" /> Scanning...
            </span>
          ) : (
            '🔍 Scan Now'
          )}
        </button>
      </div>

      {error && (
        <div className="error-card card">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{error}</span>
        </div>
      )}

      {!loading && trends.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">📡</div>
          <h3>Ready to discover?</h3>
          <p>
            Click <strong>Scan Now</strong> to run the topic discovery pipeline across multiple layers.
          </p>
        </div>
      )}

      {loading && trends.length === 0 && (
        <div className="skeleton-table">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton-row shimmer" />
          ))}
        </div>
      )}

      {!loading && trends.length > 0 && (
        <div className="results-container">
          <TrendTable trends={trends} />
        </div>
      )}
    </div>
  );
}
