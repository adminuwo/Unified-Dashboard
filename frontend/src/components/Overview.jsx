import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export const Overview = () => {
  const { authFetch } = useAuth();
  const [stats, setStats] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [playAnalytics, setPlayAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [statsRes, telemetryRes, playRes] = await Promise.all([
        authFetch('/api/admin/stats'),
        authFetch('/api/telemetry/overview'),
        authFetch('/api/admin/analytics/google-play/overview?app_codes=aisa,ailegal')
      ]);

      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
      if (telemetryRes.ok) {
        const tData = await telemetryRes.json();
        setTelemetry(tData);
      }
      if (playRes.ok) {
        const pData = await playRes.json();
        setPlayAnalytics(pData.data);
      }
    } catch (err) {
      console.error('Failed to fetch overview data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Today'],
    datasets: [
      {
        label: 'Revenue (₹)',
        data: [0, 0, 0, 0, 0, 0, stats?.total_revenue || 0],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#8b5cf6',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8' } },
    },
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
    },
  };

  if (loading && !stats) {
    return <div style={{ color: 'var(--text-muted)' }}>Loading platform analytics...</div>;
  }

  const appTenants = [
    { code: 'ailegal', name: 'AI Legal', icon: '⚖️' },
    { code: 'aisa', name: 'AISA Assistant', icon: '🤖' },
    { code: 'aiads', name: 'AI Ads Generator', icon: '📢' },
    { code: 'uwoconnect', name: 'UWO Connect', icon: '🔗' },
    { code: 'efvframework', name: 'EFV Framework', icon: '🚀' },
  ];

  return (
    <div>
      {/* Connected Applications Tenant Bar */}
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.1em', marginBottom: '10px' }}>
          Connected Application Tenants
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          {appTenants.map((app) => (
            <div
              key={app.code}
              style={{
                padding: '12px 16px',
                borderRadius: '16px',
                backgroundColor: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '18px' }}>{app.icon}</span>
                <span style={{ fontSize: '13px', fontWeight: '700', color: '#f8fafc' }}>{app.name}</span>
              </div>
              <span style={{ fontSize: '10px', fontWeight: '800', color: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.15)', padding: '2px 8px', borderRadius: '10px' }}>
                ACTIVE
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span>Total Identities</span>
            <div className="metric-icon">👥</div>
          </div>
          <div className="metric-value">{stats?.total_users || 0}</div>
          <div className="metric-sub">{stats?.verified_users || 0} verified users</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Total Revenue</span>
            <div className="metric-icon">💳</div>
          </div>
          <div className="metric-value">
            ₹{(stats?.total_revenue || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <div className="metric-sub">{stats?.active_subscriptions || 0} active subscriptions</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>App Downloads</span>
            <div className="metric-icon">📥</div>
          </div>
          <div className="metric-value">{playAnalytics?.combined?.daily_device_installs || telemetry?.total_downloads || 0}</div>
          <div className="metric-sub">All-Time Google Play Downloads</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>AI Tokens Consumed</span>
            <div className="metric-icon">🧠</div>
          </div>
          <div className="metric-value">{(telemetry?.total_tokens || 0).toLocaleString()}</div>
          <div className="metric-sub">{telemetry?.total_chat_sessions || 0} prompt sessions</div>
        </div>
      </div>

      <div className="card-section">
        <div className="section-header">
          <div className="section-title">Revenue & Subscription Activity</div>
        </div>
        <div style={{ height: '280px' }}>
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
};

