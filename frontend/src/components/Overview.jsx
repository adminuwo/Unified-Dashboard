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
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/admin/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
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

  return (
    <div>
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
            <span>Connected Apps</span>
            <div className="metric-icon">🔑</div>
          </div>
          <div className="metric-value">{stats?.total_applications || 0}</div>
          <div className="metric-sub">{stats?.active_applications || 0} active keys</div>
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
            <span>Central Logs</span>
            <div className="metric-icon">📜</div>
          </div>
          <div className="metric-value">{stats?.total_logs || 0}</div>
          <div className="metric-sub">Across connected apps</div>
        </div>
      </div>

      <div className="card-section">
        <div className="section-header">
          <div className="section-title">Revenue & Subscription Activity</div>
        </div>
        <div style={{ height: '300px' }}>
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
};
