const SOURCE_CONFIG = {
  twitter_ksa: { cls: 'twitter', emoji: '🐦', label: 'Twitter/X KSA' },
  google_trends: { cls: 'google', emoji: '📈', label: 'Google Trends' },
  gulf_news: { cls: 'news', emoji: '📰', label: 'Gulf News' },
  cultural: { cls: 'cultural', emoji: '🎭', label: 'Cultural' },
  targeted: { cls: 'targeted', emoji: '🌐', label: 'Targeted Domain' },
  youtube: { cls: 'youtube', emoji: '📹', label: 'YouTube' },
  serp_trends: { cls: 'google', emoji: '📊', label: 'SerpAPI Trends' },
  influencer: { cls: 'influencer', emoji: '🌟', label: 'Influencer Signal' },
  seed_keyword: { cls: 'seed', emoji: '🌱', label: 'Seed Keyword' },
};

function formatRelativeTime(dtStr) {
  if (!dtStr) return '-';
  const dt = new Date(dtStr);
  const diff = Date.now() - dt.getTime();
  const seconds = diff / 1000;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export default function TrendTable({ trends }) {
  if (!trends || trends.length === 0) return null;

  return (
    <div className="table-container fade-in">
      <table className="trend-table">
        <thead>
          <tr>
            <th style={{ width: '40px' }}>#</th>
            <th>Title</th>
            <th>Source</th>
            <th>Origin</th>
            <th>Jack Score</th>
            <th>Date</th>
            <th style={{ width: '40px' }}>Link</th>
          </tr>
        </thead>
        <tbody>
          {trends.map((t, i) => {
            const config = SOURCE_CONFIG[t.source] || { cls: 'news', emoji: '📰', label: t.source };
            const jackPercent = (t.jack_potential * 100).toFixed(0);
            const scoreClass = t.jack_potential >= 0.8 ? 'high' : t.jack_potential >= 0.6 ? 'medium' : 'low';

            return (
              <tr key={i}>
                <td className="text-secondary">{i + 1}</td>
                <td className="trend-title-cell">
                  {t.title}
                  {t.jack_potential >= 0.85 && <span className="hot-tag">HOT</span>}
                </td>
                <td>
                  <span className={`source-badge ${config.cls}`}>
                    {config.emoji} {config.label}
                  </span>
                </td>
                <td>
                  <span className={`origin-badge origin-${t.origin?.replace('_', '-').toLowerCase()}`}>
                    {t.origin || 'TREND'}
                  </span>
                </td>
                <td className="jack-score-cell">
                  <div className="jack-bar-container">
                    <div
                      className={`jack-bar ${scoreClass}`}
                      style={{ width: `${jackPercent}%` }}
                    />
                  </div>
                  <span className={`jack-text ${scoreClass}`}>{jackPercent}%</span>
                </td>
                <td className="text-secondary">{formatRelativeTime(t.discovered_at || t.published_at)}</td>
                <td>
                  {t.url ? (
                    <a href={t.url} target="_blank" rel="noreferrer" className="link-icon">
                      🔗
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
