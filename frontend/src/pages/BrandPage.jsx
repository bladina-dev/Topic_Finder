import { useState, useEffect, useCallback } from 'react';
import { fetchBrandProfile, uploadBrandPdf, clearBrandData } from '../api';

export default function BrandPage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [file, setFile] = useState(null);
  const [brandName, setBrandName] = useState('');

  const loadProfile = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchBrandProfile();
      if (data && data.name) {
        setProfile(data);
      }
    } catch (e) {
      console.error('Failed to load brand profile');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const handleFileChange = (e) => {
    if (e.target.files?.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      await uploadBrandPdf(file, brandName);
      setFile(null);
      setBrandName('');
      loadProfile();
    } catch (e) {
      setError(`Upload failed: ${e.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm('Are you sure you want to clear all brand data?')) return;
    try {
      await clearBrandData();
      setProfile(null);
    } catch (e) {
      setError('Failed to clear brand data');
    }
  };

  return (
    <div className="brand-page fade-in">
      <header className="page-header">
        <h1 className="page-title">Brand Profile</h1>
        <p className="page-subtitle">Train the agent on your brand strategy and messaging</p>
      </header>

      <div className="brand-layout">
        {!profile && (
          <section className="upload-container card">
            <h2 className="section-title">Upload Strategy PDF</h2>
            <div className={`upload-zone ${file ? 'has-file' : ''}`}>
              <div className="upload-icon-wrap">📄</div>
              <div className="upload-text-wrap">
                {file ? (
                  <p className="file-name">{file.name}</p>
                ) : (
                  <p className="upload-prompt">Click to browse or drag & drop brand PDF</p>
                )}
                <p className="upload-hint">The agent uses this a source of truth for all content angles</p>
              </div>
              <input 
                type="file" 
                className="file-input-hidden" 
                accept=".pdf" 
                onChange={handleFileChange} 
              />
            </div>

            <div className="upload-actions">
              <input 
                type="text" 
                placeholder="Brand Name (Optional)" 
                className="brand-input"
                value={brandName}
                onChange={e => setBrandName(e.target.value)}
              />
              <button 
                className="btn btn-primary" 
                onClick={handleUpload} 
                disabled={uploading || !file}
              >
                {uploading ? '⚙️ Processing...' : '🚀 Ingest Brand Strategy'}
              </button>
            </div>
          </section>
        )}

        {profile && (
          <div className="profile-container fade-in">
            <div className="profile-header card">
              <div className="header-info">
                <h2 className="brand-name">{profile.name}</h2>
                <span className="industry-badge">🏗️ {profile.industry}</span>
              </div>
              <button className="btn btn-danger btn-sm" onClick={handleClear}>🗑️ Clear Profile</button>
            </div>

            <div className="profile-grid">
              <section className="profile-card card">
                <h3 className="card-title">🎭 Tone of Voice</h3>
                <p className="card-content">{profile.tone}</p>
              </section>

              <section className="profile-card card">
                <h3 className="card-title">🎯 Target Audience</h3>
                <p className="card-content">{profile.audience}</p>
              </section>

              <section className="profile-card card full-width">
                <h3 className="card-title">💡 Key Messages</h3>
                <ul className="message-list">
                  {profile.key_messages?.map((msg, i) => (
                    <li key={i}>{msg}</li>
                  ))}
                </ul>
              </section>

              <section className="profile-card card">
                <h3 className="card-title">💎 Core Values</h3>
                <div className="values-grid">
                  {profile.values?.map((val, i) => (
                    <span key={i} className="value-tag">{val}</span>
                  ))}
                </div>
              </section>

              <section className="profile-card card">
                <h3 className="card-title">⚔️ Competitors</h3>
                <div className="values-grid">
                  {profile.competitors?.map((comp, i) => (
                    <span key={i} className="competitor-tag">{comp}</span>
                  ))}
                </div>
              </section>
            </div>
          </div>
        )}

        {loading && (
          <div className="skeleton-profile shimmer">
            <div className="skeleton-card" />
            <div className="skeleton-grid">
              <div className="skeleton-card" />
              <div className="skeleton-card" />
              <div className="skeleton-card" />
            </div>
          </div>
        )}

        {error && (
          <div className="error-card card">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
