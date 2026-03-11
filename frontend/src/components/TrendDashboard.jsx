export default function TrendDashboard({ trends }) {
  if (!trends || trends.length === 0) return null

  const sourceConfig = {
    twitter_ksa: { cls: 'twitter', emoji: '🐦', label: 'Twitter/X KSA' },
    google_trends: { cls: 'google', emoji: '📈', label: 'Google Trends' },
    gulf_news: { cls: 'news', emoji: '📰', label: 'Gulf News' },
    cultural: { cls: 'cultural', emoji: '🎭', label: 'Cultural' },
  }

  return (
    <div>
      <h2 className="section-title">
        📊 Trending Topics
        <span className="section-count">{trends.length}</span>
      </h2>
      <div className="trends-grid">
        {trends.map((trend, i) => {
          const src = sourceConfig[trend.source] || sourceConfig.gulf_news
          const score = trend.jack_potential || 0
          const scoreCls = score >= 0.8 ? 'high' : score >= 0.6 ? 'medium' : 'low'

          return (
            <div className="trend-card" key={i}>
              <div className="trend-header">
                <h3 className="trend-title">{trend.title}</h3>
                {score >= 0.85 && <span className="flash-badge">🔥 HOT</span>}
              </div>
              {trend.description && (
                <p className="trend-description">{trend.description}</p>
              )}
              <div className="trend-meta">
                <span className={`source-badge ${src.cls}`}>
                  {src.emoji} {src.label}
                </span>
                <span className={`jack-score ${scoreCls}`}>
                  ⚡ {(score * 100).toFixed(0)}%
                </span>
                {trend.region && (
                  <span style={{
                    fontSize: '0.7rem',
                    color: 'var(--text-dim)',
                    fontFamily: 'var(--font-mono)',
                  }}>
                    📍 {trend.region}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
