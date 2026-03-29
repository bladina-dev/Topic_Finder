import { useState } from 'react';
import { updateAngleStatus } from '../api';

const PLATFORM_CONFIG = {
  twitter: { cls: 'twitter', label: 'Twitter/X', icon: '🐦' },
  linkedin: { cls: 'linkedin', label: 'LinkedIn', icon: '💼' },
  instagram: { cls: 'instagram', label: 'Instagram', icon: '📸' },
  tiktok: { cls: 'tiktok', label: 'TikTok', icon: '📱' },
  general: { cls: 'general', label: 'General', icon: '📝' },
};

const TRIGGER_CONFIG = {
  zeigarnik: { cls: 'zeigarnik', label: 'Zeigarnik Effect', color: '#ff9800' },
  fomo: { cls: 'fomo', label: 'FOMO', color: '#f44336' },
  curiosity_gap: { cls: 'curiosity', label: 'Curiosity Gap', color: '#9c27b0' },
  social_proof: { cls: 'social', label: 'Social Proof', color: '#4caf50' },
  gain: { cls: 'gain', label: 'Benefit/Gain', color: '#009688' },
  loss_aversion: { cls: 'loss', label: 'Loss Aversion', color: '#e91e63' },
};

export default function AngleCard({ angle, trend, filenameStem }) {
  const [status, setStatus] = useState('new');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleAction = async (newStatus) => {
    setLoading(true);
    try {
      await updateAngleStatus(filenameStem, newStatus);
      setStatus(newStatus);
    } catch (e) {
      console.error('Failed to update status:', e);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    const text = `📌 ${angle.headline}\n\n🪝 ${angle.hook}\n\n💡 Source: ${trend.title}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const platform = PLATFORM_CONFIG[angle.platform] || PLATFORM_CONFIG.general;
  const alignmentScore = Math.round(angle.brand_alignment_score * 100);

  return (
    <div className={`angle-card card ${status} ${loading ? 'loading-opacity' : ''}`}>
      <div className="angle-card-header">
        <h3 className="angle-headline">{angle.headline}</h3>
        <div className="angle-score-badge" title="Brand Alignment Score">
          <svg viewBox="0 0 36 36" className="score-ring">
            <path className="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            <path className="ring-fill" strokeDasharray={`${alignmentScore}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            <text x="18" y="20.35" className="ring-text">{alignmentScore}%</text>
          </svg>
        </div>
      </div>

      <blockquote className="angle-hook">
        {angle.hook}
      </blockquote>

      <div className="angle-body-section">
        <p className="body-title">Body Outline</p>
        <div className="body-outline-text">{angle.body_outline}</div>
      </div>

      <div className="angle-tags">
        <span className={`platform-badge ${platform.cls}`}>
          {platform.icon} {platform.label}
        </span>
        {angle.psych_triggers?.map((t, idx) => {
          const cfg = TRIGGER_CONFIG[t.type] || { label: t.type, color: '#888' };
          return (
            <span key={idx} className="trigger-badge" style={{ borderColor: cfg.color, color: cfg.color }}>
              🧠 {cfg.label}
            </span>
          );
        })}
      </div>

      <div className="angle-actions">
        <button 
          className={`btn btn-sm btn-approve ${status === 'approved' ? 'active' : ''}`}
          onClick={() => handleAction('approved')}
          disabled={loading || status === 'approved'}
        >
          {status === 'approved' ? '✓ Approved' : '✅ Approve'}
        </button>
        <button 
          className={`btn btn-sm btn-skip ${status === 'skipped' ? 'active' : ''}`}
          onClick={() => handleAction('skipped')}
          disabled={loading || status === 'skipped'}
        >
          {status === 'skipped' ? '✕ Skipped' : '❌ Skip'}
        </button>
        <button className="btn btn-sm" onClick={copyToClipboard}>
          {copied ? '📋 Copied!' : '📋 Copy'}
        </button>
      </div>
    </div>
  );
}
