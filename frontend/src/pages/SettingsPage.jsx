import { useState, useEffect, useCallback } from 'react';
import ApiKeyInput from '../components/ApiKeyInput';
import { fetchSettings, updateSettings, fetchHealth } from '../api';

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    try {
      const [settingsData, healthData] = await Promise.all([
        fetchSettings(),
        fetchHealth()
      ]);
      setSettings(settingsData);
      setHealth(healthData);
    } catch (e) {
      setError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleUpdate = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setSuccess(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess(false);
    try {
      await updateSettings(settings);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      loadSettings(); // Refresh (masked keys)
    } catch (e) {
      setError(`Save failed: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading && !settings) {
    return (
      <div className="settings-page loading-state">
        <span className="spinner" /> Loading configuration...
      </div>
    );
  }

  return (
    <div className="settings-page fade-in">
      <header className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Configure API keys, AI provider, and scan preferences</p>
      </header>

      <div className="settings-layout">
        <section className="settings-section card">
          <h2 className="section-title">API Key Management</h2>
          <div className="api-keys-grid">
            <ApiKeyInput 
              label="Tavily Search API" 
              value={settings.tavily_api_key} 
              onChange={val => handleUpdate('tavily_api_key', val)}
            />
            <ApiKeyInput 
              label="SerpAPI Google Trends" 
              value={settings.serpapi_api_key} 
              onChange={val => handleUpdate('serpapi_api_key', val)}
            />
            <ApiKeyInput 
              label="YouTube Data API" 
              value={settings.youtube_data_api_key} 
              onChange={val => handleUpdate('youtube_data_api_key', val)}
            />
            <ApiKeyInput 
              label="Anthropic Claude" 
              value={settings.anthropic_api_key} 
              onChange={val => handleUpdate('anthropic_api_key', val)}
            />
            <ApiKeyInput 
              label="Notion API Token" 
              value={settings.notion_api_key} 
              onChange={val => handleUpdate('notion_api_key', val)}
            />
            <ApiKeyInput 
              label="Telegram Bot Token" 
              value={settings.telegram_bot_token} 
              onChange={val => handleUpdate('telegram_bot_token', val)}
            />
            <ApiKeyInput 
              label="Azure Speech Key" 
              value={settings.azure_speech_key} 
              onChange={val => handleUpdate('azure_speech_key', val)}
            />
          </div>
        </section>

        <section className="settings-section card">
          <h2 className="section-title">Agent Configuration</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Default AI Provider</label>
              <select 
                value={settings.default_ai_provider} 
                onChange={e => handleUpdate('default_ai_provider', e.target.value)}
              >
                <option value="gemini">Google Gemini</option>
                <option value="claude">Anthropic Claude</option>
                <option value="lmstudio">LM Studio</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Agent Timezone</label>
              <input 
                type="text" 
                value={settings.agent_timezone} 
                onChange={e => handleUpdate('agent_timezone', e.target.value)}
                placeholder="UTC+3"
              />
            </div>

            <div className="form-group">
              <label>YouTube Scan Enabled</label>
              <div className="check-toggle">
                <input 
                  type="checkbox" 
                  checked={settings.youtube_scan_enabled} 
                  onChange={e => handleUpdate('youtube_scan_enabled', e.target.checked)}
                />
                <span className="check-label">{settings.youtube_scan_enabled ? 'Yes' : 'No'}</span>
              </div>
            </div>

            <div className="form-group">
              <label>Google Trends Enabled</label>
              <div className="check-toggle">
                <input 
                  type="checkbox" 
                  checked={settings.google_trends_enabled} 
                  onChange={e => handleUpdate('google_trends_enabled', e.target.checked)}
                />
                <span className="check-label">{settings.google_trends_enabled ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>
        </section>

        {health && (
          <section className="settings-section card status-matrix-card">
            <h2 className="section-title">Connectivity Health</h2>
            <div className="status-matrix">
              {Object.entries(health.apis || {}).map(([api, ok]) => (
                <div key={api} className="status-item">
                  <span className={`status-dot ${ok ? 'ok' : 'err'}`} />
                  <span className="status-label">{api}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="settings-footer">
          {error && <div className="error-badge">{error}</div>}
          {success && <div className="success-badge">✅ Settings saved to .env</div>}
          <button 
            className="btn btn-primary btn-lg save-settings-btn" 
            onClick={handleSave} 
            disabled={saving}
          >
            {saving ? '⌛ Saving...' : '💾 Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  );
}
