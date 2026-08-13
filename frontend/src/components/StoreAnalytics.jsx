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

export const StoreAnalytics = () => {
  const { authFetch } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [projectFilter, setProjectFilter] = useState('ALL');
  const [dateRange, setDateRange] = useState('30d');
  const [feedback, setFeedback] = useState(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams({
        project: projectFilter,
        date_range: dateRange
      });
      const res = await authFetch(`/api/admin/store-analytics?${query.toString()}`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      } else {
        setFeedback({ type: 'error', message: 'Failed to load store analytics metrics.' });
      }
    } catch (err) {
      console.error('Failed to fetch store analytics:', err);
      setFeedback({ type: 'error', message: 'Network error fetching analytics.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [projectFilter, dateRange]);

  const handleSyncNow = async () => {
    setSyncing(true);
    setFeedback(null);
    try {
      const res = await authFetch('/api/admin/store-analytics/sync', {
        method: 'POST'
      });
      const json = await res.json();
      if (res.ok) {
        setFeedback({
          type: json.success ? 'success' : 'warning',
          message: json.message
        });
        await fetchAnalytics();
      } else {
        setFeedback({ type: 'error', message: 'Failed to trigger store sync.' });
      }
    } catch (err) {
      console.error('Failed to sync store analytics:', err);
      setFeedback({ type: 'error', message: 'Sync failed due to network exception.' });
    } finally {
      setSyncing(false);
    }
  };

  const aisaProject = data?.projects?.find((p) => p.project === 'AISA');
  const aiLegalProject = data?.projects?.find((p) => p.project === 'AI_LEGAL');

  const chartLabels = data?.timeline?.map((t) => t.date) || [];
  const aisaSeries = data?.timeline?.map((t) => t.aisa) || [];
  const aiLegalSeries = data?.timeline?.map((t) => t.ai_legal) || [];
  const totalSeries = data?.timeline?.map((t) => t.total) || [];

  const getDatasets = () => {
    if (projectFilter === 'AISA') {
      return [
        {
          label: 'AISA Installs (com.uwo.aisa)',
          data: aisaSeries,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.15)',
          fill: true,
          tension: 0.4
        }
      ];
    }
    if (projectFilter === 'AI_LEGAL') {
      return [
        {
          label: 'AI Legal Installs (com.uwo.ailegal)',
          data: aiLegalSeries,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          fill: true,
          tension: 0.4
        }
      ];
    }
    return [
      {
        label: 'AISA (com.uwo.aisa)',
        data: aisaSeries,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: false,
        tension: 0.4
      },
      {
        label: 'AI Legal (com.uwo.ailegal)',
        data: aiLegalSeries,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: false,
        tension: 0.4
      },
      {
        label: 'Combined Total',
        data: totalSeries,
        borderColor: '#8b5cf6',
        borderDash: [5, 5],
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4
      }
    ];
  };

  const chartData = {
    labels: chartLabels,
    datasets: getDatasets()
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8' } }
    },
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }
    }
  };

  return (
    <div>
      {feedback && (
        <div
          className={`alert-banner ${feedback.type}`}
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            background: feedback.type === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            border: `1px solid ${feedback.type === 'error' ? '#ef4444' : '#10b981'}`,
            color: '#f8fafc',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>{feedback.message}</span>
          <button
            onClick={() => setFeedback(null)}
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '16px' }}
          >
            ✕
          </button>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
            className="filter-select"
            style={{
              background: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '8px 14px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Projects</option>
            <option value="AISA">AISA (com.uwo.aisa)</option>
            <option value="AI_LEGAL">AI Legal (com.uwo.ailegal)</option>
          </select>

          <div style={{ display: 'flex', background: '#1e293b', padding: '4px', borderRadius: '6px', border: '1px solid #334155' }}>
            {['7d', '30d', '90d'].map((r) => (
              <button
                key={r}
                onClick={() => setDateRange(r)}
                style={{
                  background: dateRange === r ? '#6366f1' : 'transparent',
                  color: dateRange === r ? '#ffffff' : '#94a3b8',
                  border: 'none',
                  padding: '6px 14px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: '500'
                }}
              >
                {r === '7d' ? '7 Days' : r === '30d' ? '30 Days' : '90 Days'}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleSyncNow}
          disabled={syncing}
          className="btn-primary"
          style={{
            background: '#6366f1',
            color: '#fff',
            border: 'none',
            padding: '10px 18px',
            borderRadius: '6px',
            cursor: syncing ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          {syncing ? '🔄 Syncing Google Play...' : '⚡ Sync Google Play Data'}
        </button>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span>Overall Android Installs</span>
            <div className="metric-icon">📱</div>
          </div>
          <div className="metric-value">{data?.total_android_downloads?.toLocaleString() || 0}</div>
          <div className="metric-sub">Google Play Console Total</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>AISA Installs</span>
            <div className="metric-icon">⚡</div>
          </div>
          <div className="metric-value">{aisaProject?.total_downloads?.toLocaleString() || 0}</div>
          <div className="metric-sub">com.uwo.aisa</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>AI Legal Installs</span>
            <div className="metric-icon">⚖️</div>
          </div>
          <div className="metric-value">{aiLegalProject?.total_downloads?.toLocaleString() || 0}</div>
          <div className="metric-sub">com.uwo.ailegal</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Sync Status</span>
            <div className="metric-icon">🔄</div>
          </div>
          <div className="metric-value" style={{ fontSize: '18px', color: data?.sync_status === 'success' ? '#10b981' : '#f59e0b' }}>
            {data?.sync_status?.toUpperCase() || 'IDLE'}
          </div>
          <div className="metric-sub">
            {data?.last_synced_at ? new Date(data.last_synced_at).toLocaleString() : 'Not Synced Yet'}
          </div>
        </div>
      </div>

      <div className="card-section" style={{ marginTop: '24px' }}>
        <div className="section-header">
          <div className="section-title">Google Play Installs & Downloads Analytics</div>
        </div>
        <div style={{ height: '320px' }}>
          {loading ? (
            <div style={{ color: 'var(--text-muted)', paddingTop: '40px', textAlign: 'center' }}>
              Loading Store Analytics...
            </div>
          ) : (
            <Line data={chartData} options={chartOptions} />
          )}
        </div>
      </div>
    </div>
  );
};
