import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const ChatTrackingTab = () => {
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
                border: selectedApp === app ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.1)',
                backgroundColor: selectedApp === app ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                color: selectedApp === app ? '#818cf8' : '#94a3b8',
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
            <span>Total Chat Sessions</span>
            <div className="metric-icon">💬</div>
          </div>
          <div className="metric-value">{telemetry?.total_chat_sessions || 0}</div>
          <div className="metric-sub">Active prompt interactions</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Total Tokens Consumed</span>
            <div className="metric-icon">🧠</div>
          </div>
          <div className="metric-value">{(telemetry?.total_tokens || 0).toLocaleString()}</div>
          <div className="metric-sub">Input + output token total</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Average Latency</span>
            <div className="metric-icon">⏱️</div>
          </div>
          <div className="metric-value">{telemetry?.avg_latency_ms || 0} ms</div>
          <div className="metric-sub">Mean response time</div>
        </div>
      </div>

      {/* AI Model Share Distribution Table */}
      <div className="card-section" style={{ marginTop: '24px' }}>
        <div className="section-header">
          <div className="section-title">AI Model Share & Token Usage</div>
        </div>

        {loading ? (
          <div style={{ color: 'var(--text-muted)' }}>Loading model analytics...</div>
        ) : !telemetry?.model_share || telemetry.model_share.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>
            No chat tracking events logged yet for selected filter.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>AI Model</th>
                <th>Request Count</th>
                <th>Total Tokens Consumed</th>
                <th>Usage Share</th>
              </tr>
            </thead>
            <tbody>
              {telemetry.model_share.map((m, idx) => {
                const percentage = telemetry.total_tokens > 0 ? ((m.tokens / telemetry.total_tokens) * 100).toFixed(1) : '0.0';
                return (
                  <tr key={idx}>
                    <td>
                      <span style={{ fontWeight: '700', color: '#f8fafc' }}>⚡ {m.model}</span>
                    </td>
                    <td>{m.count.toLocaleString()}</td>
                    <td>{m.tokens.toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '100px', height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                          <div style={{ width: `${percentage}%`, height: '100%', backgroundColor: '#6366f1' }} />
                        </div>
                        <span style={{ fontSize: '12px', fontWeight: '600', color: '#818cf8' }}>{percentage}%</span>
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
