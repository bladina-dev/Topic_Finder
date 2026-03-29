import { useState } from 'react';

export default function ApiKeyInput({ label, value, onChange, placeholder = '****xxxx' }) {
  const [show, setShow] = useState(false);
  const isConfigured = value && value !== '';

  return (
    <div className="api-key-group">
      <div className="api-key-header">
        <label className="api-key-label">{label}</label>
        <span className={`api-status-dot ${isConfigured ? 'configured' : 'missing'}`} title={isConfigured ? 'Configured' : 'Missing Key'} />
      </div>
      <div className="api-key-input-wrapper">
        <input
          type={show ? 'text' : 'password'}
          className="api-key-input"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <button 
          type="button" 
          className="btn-toggle-visibility" 
          onClick={() => setShow(!show)}
          title={show ? 'Hide Key' : 'Show Key'}
        >
          {show ? '👁️' : '🙈'}
        </button>
      </div>
    </div>
  );
}
