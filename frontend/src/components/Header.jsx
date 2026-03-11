export default function Header() {
  const now = new Date()
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })

  return (
    <header className="header">
      <div className="header-left">
        <div>
          <div className="header-logo">Marketing Agent</div>
          <div className="header-subtitle">Autonomous Content Command Center</div>
        </div>
      </div>
      <div className="header-status">
        <div className="status-dot" />
        <span>Online</span>
        <span style={{ color: 'var(--text-dim)', margin: '0 4px' }}>·</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
          {dateStr} {timeStr}
        </span>
        <span style={{ color: 'var(--text-dim)', margin: '0 4px' }}>·</span>
        <span style={{ fontSize: '0.8rem' }}>Next run: 6:00 PM</span>
      </div>
    </header>
  )
}
