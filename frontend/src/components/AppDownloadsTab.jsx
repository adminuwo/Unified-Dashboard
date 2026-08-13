import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const AppDownloadsTab = () => {
  const { authFetch } = useAuth();
  const [telemetry, setTelemetry] = useState(null);
  const [selectedApp, setSelectedApp] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchTelemetry = async () => {
    setLoading(true);
    try {
      const url = selectedApp === 'all' ? '/api/telemetry/overview' : `/api/telemetry/overview?app_code=${selectedApp}`;
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (err) {
      console.error('Failed to fetch telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, [selectedApp]);

  return (
    <div>
      {/* App Code Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['all', 'ailegal', 'aisa', 'aiads', 'uwoconnect', 'efvframework'].map((app) => (
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
          <div className="metric-value">{telemetry?.total_downloads || 0}</div>
          <div className="metric-sub">Cumulative installs & downloads</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Android Installs</span>
            <div className="metric-icon">🤖</div>
          </div>
          <div className="metric-value">{telemetry?.downloads_by_platform?.android || 0}</div>
          <div className="metric-sub">Play Store & APK</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>iOS & Desktop</span>
            <div className="metric-icon">🍏</div>
          </div>
          <div className="metric-value">
            {(telemetry?.downloads_by_platform?.ios || 0) + (telemetry?.downloads_by_platform?.windows || 0)}
          </div>
          <div className="metric-sub">App Store & Windows EXE</div>
        </div>
      </div>

      {/* Platform Distribution Table */}
      <div className="card-section" style={{ marginTop: '24px' }}>
        <div className="section-header">
          <div className="section-title">Platform Breakdown</div>
        </div>

        {loading ? (
          <div style={{ color: 'var(--text-muted)' }}>Loading download metrics...</div>
        ) : !telemetry?.downloads_by_platform || Object.keys(telemetry.downloads_by_platform).length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
            No download events recorded yet for selected filter.
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
              {Object.entries(telemetry.downloads_by_platform).map(([platform, count], idx) => {
                const percentage = telemetry.total_downloads > 0 ? ((count / telemetry.total_downloads) * 100).toFixed(1) : '0.0';
                return (
                  <tr key={idx}>
                    <td>
                      <span style={{ fontWeight: '700', color: '#f8fafc', textTransform: 'uppercase' }}>
                        📱 {platform}
                      </span>
                    </td>
                    <td>{count.toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '100px', height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                          <div style={{ width: `${percentage}%`, height: '100%', backgroundColor: '#10b981' }} />
                        </div>
                        <span style={{ fontSize: '12px', fontWeight: '600', color: '#34d399' }}>{percentage}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
