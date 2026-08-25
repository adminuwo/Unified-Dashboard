import React from 'react';
import { useAuth } from '../context/AuthContext';

export const Sidebar = ({ currentTab, setTab }) => {
  const { adminUsername, logout } = useAuth();

  const navItems = [
    { id: 'unified_analytics', label: 'Unified Analytics', icon: '🌐' },
    { id: 'overview', label: 'Overview', icon: '📊' },
    // { id: 'overlap', label: 'App Analytics', icon: '📈' },
    // { id: 'auth_tester', label: 'Auth Service', icon: '🔒' },
    { id: 'applications', label: 'Application Keys', icon: '🔑' },
    { id: 'chat_tracking', label: 'Chat Tracking', icon: '💬' },
    { id: 'app_downloads', label: 'App Downloads', icon: '📥' },
    { id: 'users', label: 'User Directory', icon: '👥' },
    { id: 'revenue', label: 'Revenue & Plans', icon: '💳' },
    { id: 'logs', label: 'Central Logs', icon: '📜' },
    { id: 'sandbox', label: 'API Sandbox', icon: '⚡' },
  ];


  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">⚡</div>
        <div className="brand-text">
          <h1>Unified Platform</h1>
          <span>Central Shared Backend</span>
        </div>
      </div>

      <ul className="nav-list">
        {navItems.map((item) => (
          <li
            key={item.id}
            className={`nav-item ${currentTab === item.id ? 'active' : ''}`}
            onClick={() => setTab(item.id)}
          >
            <span>{item.icon}</span>
            {item.label}
          </li>
        ))}
      </ul>

      <div className="sidebar-footer">
        <div className="admin-badge">
          <div className="admin-info">
            <span className="admin-name">{adminUsername || 'Master Admin'}</span>
            <span className="admin-role">● Online (Master)</span>
          </div>
          <button className="btn-logout" onClick={logout}>
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
};
