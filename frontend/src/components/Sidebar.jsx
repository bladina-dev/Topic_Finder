import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { fetchHealth } from '../api';

const NAV_ITEMS = [
  { path: '/', label: 'Discovery', icon: '🔍' },
  { path: '/angles', label: 'Content Angles', icon: '✍️' },
  { path: '/sources', label: 'Sources', icon: '📋' },
  { path: '/brand', label: 'Brand Profile', icon: '📄' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  const [healthy, setHealthy] = useState(true);

  useEffect(() => {
    fetchHealth()
      .then(data => setHealthy(data.status === 'healthy'))
      .catch(() => setHealthy(false));
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="logo-icon">⚡</span>
        <span className="logo-text">Marketing Agent</span>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className={`health-dot ${healthy ? 'healthy' : 'unhealthy'}`} title={healthy ? 'FastAPI Connected' : 'API Error'} />
        <span className="health-label">{healthy ? 'Healthy' : 'Disconnected'}</span>
      </div>
    </aside>
  );
}
