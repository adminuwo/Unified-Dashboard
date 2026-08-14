import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const AppDownloadsTab = () => {
  const { authFetch } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [selectedApp, setSelectedApp] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      // Calculate a 30-day date range
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - 30);
      
      const startStr = start.toISOString().split('T')[0];
      const endStr = end.toISOString().split('T')[0];
      
      const appCodes = selectedApp === 'all' ? 'aisa,ailegal' : selectedApp;
      
      const url = `/api/admin/analytics/google-play/overview?app_codes=${appCodes}&start_date=${startStr}&end_date=${endStr}`;
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [selectedApp]);

  // Safely extract the combined stats from our new backend
  const combined = analytics?.combined || {};
  const totalDownloads = combined.daily_device_installs || 0;
  const androidInstalls = combined.daily_device_installs || 0;
  const iosInstalls = 0; // Coming soon in Phase 4!

  return (
    <div>
      {/* App Code Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['all', 'ailegal', 'aisa'].map((app) => (
            <button
              key={app}
              onClick={() => setSelectedApp(app)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: selectedApp === app ? '1px solid #10b981' : '1px solid rgba(255, 255, 255, 0.1)',
                backgroundColor: selectedApp === app ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                color: selectedApp === app ? '#34d399' : '#94a3b8',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer',
                textTransform: 'uppercase'
              }}
            >
              {app === 'all' ? 'All Applications' : app}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span>Total App Downloads</span>
            <div className="metric-icon">📥</div>
          </div>
          <div className="metric-value">{totalDownloads.toLocaleString()}</div>
          <div className="metric-sub">Last 30 Days (Google Play)</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Android Installs</span>
            <div className="metric-icon">🤖</div>
          </div>
          <div className="metric-value">{androidInstalls.toLocaleString()}</div>
          <div className="metric-sub">Play Store Only</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>iOS & Desktop</span>
            <div className="metric-icon">🍏</div>
          </div>
          <div className="metric-value">{iosInstalls}</div>
          <div className="metric-sub">App Store Analytics (Coming Phase 4)</div>
        </div>
      </div>

      {/* Platform Distribution Table */}
      <div className="card-section" style={{ marginTop: '24px' }}>
        <div className="section-header">
          <div className="section-title">Platform Breakdown</div>
        </div>

        {loading ? (
          <div style={{ color: 'var(--text-muted)' }}>Loading download metrics...</div>
        ) : totalDownloads === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
            No download events recorded in the last 30 days.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Platform / OS</th>
                <th>Download Count</th>
                <th>Distribution Share</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <span style={{ fontWeight: '700', color: '#f8fafc', textTransform: 'uppercase' }}>
                    📱 android
                  </span>
                </td>
                <td>{androidInstalls.toLocaleString()}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '100px', height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                      <div style={{ width: `100%`, height: '100%', backgroundColor: '#10b981' }} />
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: '600', color: '#34d399' }}>100%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
