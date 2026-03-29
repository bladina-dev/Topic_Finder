import { useState, useEffect, useCallback } from 'react';
import { fetchSources, fetchSourceEntries, addSourceEntry, fetchSeedKeywords } from '../api';

export default function SourcesPage() {
  const [sourceFiles, setSourceFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState('');

  // Form state
  const [newEntry, setNewEntry] = useState({
    vertical: 'general',
    source_type: 'domain',
    handle_or_domain: '',
    label: '',
  });

  const loadFileList = useCallback(async () => {
    try {
      const data = await fetchSources();
      const raw = data.sources || [];
      // API returns [{name, path, count}, ...] — normalize to [{name, count}]
      const normalized = raw.map(s => typeof s === 'string' ? { name: s, count: 0 } : s);
      setSourceFiles(normalized);
      if (normalized.length > 0 && !selectedFile) {
        setSelectedFile(normalized[0].name);
      }
    } catch (e) {
      setError('Failed to load sources list');
    }
  }, [selectedFile]);

  const loadEntries = useCallback(async (fileName) => {
    if (!fileName) return;
    setLoading(true);
    setError('');
    try {
      if (fileName === 'seed_keywords.csv') {
        const data = await fetchSeedKeywords(fileName);
        // Map seeds to common table format
        setEntries(data.keywords?.map(k => ({
          vertical: k.vertical,
          source_type: 'seed',
          handle_or_domain: k.keyword,
          label: k.intent || k.label || '',
        })) || []);
      } else {
        const data = await fetchSourceEntries(fileName);
        setEntries(data.entries || []);
      }
    } catch (e) {
      setError(`Failed to load entries for ${fileName}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFileList();
  }, [loadFileList]);

  useEffect(() => {
    loadEntries(selectedFile);
  }, [selectedFile, loadEntries]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newEntry.handle_or_domain) return;
    
    setAdding(true);
    try {
      await addSourceEntry(selectedFile, newEntry);
      setNewEntry(prev => ({ ...prev, handle_or_domain: '', label: '' }));
      loadEntries(selectedFile);
    } catch (e) {
      setError('Failed to add source entry');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="sources-page fade-in">
      <header className="page-header">
        <h1 className="page-title">Source Manager</h1>
        <p className="page-subtitle">Manage discovery targets and content pillars</p>
      </header>

      <div className="sources-layout">
        <aside className="sources-sidebar card">
          <h3 className="sidebar-title">Source Files</h3>
          <div className="file-list">
            {sourceFiles.map(file => (
              <button
                key={file.name}
                className={`file-item ${selectedFile === file.name ? 'active' : ''}`}
                onClick={() => setSelectedFile(file.name)}
              >
                <span className="file-icon">📄</span>
                <span className="file-name">{file.name}</span>
                {file.count > 0 && <span className="section-count">{file.count}</span>}
              </button>
            ))}
          </div>
        </aside>

        <main className="sources-main">
          {error && (
            <div className="error-card card">
              <span className="error-icon">⚠️</span>
              <span className="error-message">{error}</span>
            </div>
          )}

          <section className="entries-section card">
            <div className="section-header">
              <h3 className="section-title">
                Entries in <span className="text-accent">{selectedFile}</span>
                <span className="section-count">{entries.length}</span>
              </h3>
            </div>

            <div className="table-wrapper">
              <table className="entries-table">
                <thead>
                  <tr>
                    <th>Vertical</th>
                    <th>Type</th>
                    <th>Handle / Domain</th>
                    <th>Label</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    [...Array(5)].map((_, i) => (
                      <tr key={i} className="skeleton-row shimmer">
                        <td colSpan="4"></td>
                      </tr>
                    ))
                  ) : entries.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="empty-row">No entries found in this file.</td>
                    </tr>
                  ) : (
                    entries.map((entry, i) => (
                      <tr key={i}>
                        <td><span className="vertical-tag">{entry.vertical}</span></td>
                        <td><span className="type-tag">{entry.source_type}</span></td>
                        <td className="font-mono">{entry.handle_or_domain}</td>
                        <td className="text-secondary">{entry.label}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {!(typeof selectedFile === 'string' && selectedFile.includes('seed')) && (
            <section className="add-source-section card">
              <h3 className="section-title">Add New Source</h3>
              <form className="add-source-form" onSubmit={handleAdd}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Vertical</label>
                    <select
                      value={newEntry.vertical}
                      onChange={e => setNewEntry(prev => ({ ...prev, vertical: e.target.value }))}
                    >
                      {['general', 'tech', 'finance', 'lifestyle', 'food', 'media', 'ecommerce', 'government', 'culture', 'sports'].map(v => (
                        <option key={v} value={v}>{v}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Type</label>
                    <select
                      value={newEntry.source_type}
                      onChange={e => setNewEntry(prev => ({ ...prev, source_type: e.target.value }))}
                    >
                      {['domain', 'youtube', 'twitter', 'instagram', 'tiktok'].map(t => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Handle / Domain</label>
                    <input
                      type="text"
                      placeholder="e.g. techcrunch.com or @handle"
                      value={newEntry.handle_or_domain}
                      onChange={e => setNewEntry(prev => ({ ...prev, handle_or_domain: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Label</label>
                    <input
                      type="text"
                      placeholder="Optional label"
                      value={newEntry.label}
                      onChange={e => setNewEntry(prev => ({ ...prev, label: e.target.value }))}
                    />
                  </div>
                </div>
                <button type="submit" className="btn btn-primary" disabled={adding || !newEntry.handle_or_domain}>
                  {adding ? 'Adding...' : '➕ Add Source Entry'}
                </button>
              </form>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
