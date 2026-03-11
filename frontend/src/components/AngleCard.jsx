export default function AngleCard({ angle, index }) {
  const triggerEmojis = {
    zeigarnik: '🔄',
    fomo: '⏰',
    curiosity_gap: '🧩',
    social_proof: '👥',
    gain: '📈',
    loss_aversion: '🛡️',
  }

  return (
    <div className="angle-card">
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-sm)', marginBottom: 'var(--space-xs)' }}>
        <span style={{
          fontSize: '0.7rem',
          fontWeight: 700,
          color: 'var(--accent-primary)',
          fontFamily: 'var(--font-mono)',
        }}>
          ANGLE {index}
        </span>
      </div>
      <h4 className="angle-headline">{angle.headline}</h4>
      <p className="angle-hook">"{angle.hook}"</p>
      {angle.body_outline && (
        <p className="angle-body">{angle.body_outline}</p>
      )}
      <div className="angle-meta">
        {/* Psychological Triggers */}
        {angle.psych_triggers && angle.psych_triggers.map((trigger, i) => (
          <span className="trigger-badge" key={i}>
            {triggerEmojis[trigger.type] || '🧠'} {(trigger.type || '').replace('_', ' ')}
          </span>
        ))}

        {/* Platform */}
        {angle.platform && (
          <span className="platform-badge">
            {angle.platform === 'twitter' ? '🐦' :
             angle.platform === 'instagram' ? '📸' :
             angle.platform === 'linkedin' ? '💼' :
             angle.platform === 'tiktok' ? '🎵' : '🌐'}{' '}
            {angle.platform}
          </span>
        )}

        {/* Brand Alignment Score */}
        {angle.brand_alignment_score > 0 && (
          <span className="alignment-score">
            🎯 {(angle.brand_alignment_score * 100).toFixed(0)}% fit
          </span>
        )}
      </div>

      {/* Trigger Rationale (expandable) */}
      {angle.psych_triggers && angle.psych_triggers.length > 0 && angle.psych_triggers[0].rationale && (
        <div style={{
          marginTop: 'var(--space-sm)',
          padding: 'var(--space-sm) var(--space-md)',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--border-radius-sm)',
          fontSize: '0.8rem',
          color: 'var(--text-dim)',
          fontStyle: 'italic',
        }}>
          💡 {angle.psych_triggers[0].rationale}
        </div>
      )}
    </div>
  )
}
