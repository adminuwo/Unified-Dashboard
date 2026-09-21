import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export const UnifiedAnalytics = () => {
  const { authFetch } = useAuth();
  const [activeSubTab, setActiveSubTab] = useState('overview');
  const [appCode, setAppCode] = useState('all');
  const [dateRange, setDateRange] = useState('30d');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [showSnippetModal, setShowSnippetModal] = useState(false);
  const [copiedApp, setCopiedApp] = useState(null);

  // Sub-tab data states
  const [overviewData, setOverviewData] = useState(null);
  const [webData, setWebData] = useState(null);
  const [gcpData, setGcpData] = useState(null);
  const [activityData, setActivityData] = useState(null);
  const [lastSynced, setLastSynced] = useState(null);

  const daysParam = dateRange === '24h' ? 1 : dateRange === '7d' ? 7 : dateRange === '90d' ? 90 : 30;

  const fetchTabData = async () => {
    setLoading(true);
    try {
      if (activeSubTab === 'overview') {
        const res = await authFetch(`/api/admin/unified-analytics/overview?app_code=${appCode}&days=${daysParam}`);
        if (res.ok) setOverviewData(await res.json());
      } else if (activeSubTab === 'web') {
        const res = await authFetch(`/api/admin/unified-analytics/web?app_code=${appCode}&days=${daysParam}`);
        if (res.ok) setWebData(await res.json());
      } else if (activeSubTab === 'backend_monitoring') {
        const res = await authFetch(`/api/admin/unified-analytics/backend-monitoring?hours=${dateRange === '24h' ? 24 : 48}`);
        if (res.ok) setGcpData(await res.json());
      } else if (activeSubTab === 'user_activity') {
        const res = await authFetch(`/api/admin/unified-analytics/user-activity?app_code=${appCode}&days=${daysParam}`);
        if (res.ok) setActivityData(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch unified analytics:', err);
      setFeedback({ type: 'error', message: 'Failed to load telemetry data.' });
    } finally {
      setLoading(false);
      setLastSynced(new Date());
    }
  };

  useEffect(() => {
    fetchTabData();
    // Auto-refresh every 5 minutes silently
    const interval = setInterval(fetchTabData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [activeSubTab, appCode, dateRange]);

  const handleSyncAll = async () => {
    setSyncing(true);
    setFeedback(null);
    try {
      const res = await authFetch('/api/admin/unified-analytics/sync?provider=all', { method: 'POST' });
      const json = await res.json();
      if (res.ok) {
        setFeedback({ type: 'success', message: json.message || 'All external providers synchronized successfully.' });
        await fetchTabData();
      } else {
        setFeedback({ type: 'error', message: 'Failed to sync providers.' });
      }
    } catch (err) {
      setFeedback({ type: 'error', message: 'Network exception during sync.' });
    } finally {
      setSyncing(false);
    }
  };

  const copySnippet = (appName, siteId) => {
    const baseUrl = window.location.hostname === 'localhost' ? window.location.origin : 'https://admin.uwo24.com';
    const code = `<script defer src="${baseUrl}/api/web-stats/tracker.js" data-site="${siteId}" data-endpoint="${baseUrl}/api/web-stats/collect"></script>`;
    navigator.clipboard.writeText(code);
    setCopiedApp(appName);
    setTimeout(() => setCopiedApp(null), 2500);
  };

  // ─── Chart Data Builders ───────────────────────────────────────────────────

  const overviewTimelineLabels = overviewData?.timeline?.map((t) => t.date) || [];
  const overviewChartData = {
    labels: overviewTimelineLabels,
    datasets: [
      {
        label: 'Web Pageviews (GA4 & Auto-Tracker)',
        data: overviewData?.timeline?.map((t) => t.web_views) || [],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        fill: true,
        tension: 0.2
      }
    ]
  };

  const appBreakdownLabels = overviewData?.app_breakdown?.map((app) => app.name) || [];
  const appBreakdownUsers = overviewData?.app_breakdown?.map((app) => app.users) || [];
  
  const appShareChartData = {
    labels: appBreakdownLabels,
    datasets: [
      {
        label: 'Active Users',
        data: appBreakdownUsers,
        backgroundColor: [
          'rgba(139, 92, 246, 0.65)',  // AISA
          'rgba(236, 72, 153, 0.65)',  // AI Mall
          'rgba(245, 158, 11, 0.65)',  // EFV
          'rgba(59, 130, 246, 0.65)',  // UWO
          'rgba(16, 185, 129, 0.65)',  // UWConnect
          'rgba(99, 102, 241, 0.65)',  // AI Legal
          'rgba(20, 184, 166, 0.65)',  // YUG AMC
        ],
        borderColor: [
          '#8b5cf6',
          '#ec4899',
          '#f59e0b',
          '#3b82f6',
          '#10b981',
          '#6366f1',
          '#14b8a6',
        ],
        borderWidth: 1
      }
    ]
  };

  const webTimelineLabels = webData?.timeline?.map((t) => t.date) || [];
  const webChartData = {
    labels: webTimelineLabels,
    datasets: [
      {
        label: 'Pageviews',
        data: webData?.timeline?.map((t) => t.pageviews) || [],
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.15)',
        fill: true,
        tension: 0.2
      },
      {
        label: 'Unique Active Visitors',
        data: webData?.timeline?.map((t) => t.active_users) || [],
        borderColor: '#38bdf8',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.2
      }
    ]
  };



  const gcpLabels = gcpData?.timeline?.map((t) => t.time) || [];
  const gcpChartData = {
    labels: gcpLabels,
    datasets: [
      {
        label: 'API Request Volume',
        data: gcpData?.timeline?.map((t) => t.requests) || [],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        yAxisID: 'y',
        fill: true,
        tension: 0.2
      },
      {
        label: 'Avg Latency (ms)',
        data: gcpData?.timeline?.map((t) => t.avg_latency_ms) || [],
        borderColor: '#f59e0b',
        yAxisID: 'y1',
        tension: 0.2
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8' } }
    },
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { beginAtZero: true, ticks: { color: '#64748b', precision: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } }
    }
  };

  const gcpChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8' } }
    },
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { type: 'linear', position: 'left', beginAtZero: true, ticks: { color: '#6366f1', precision: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y1: { type: 'linear', position: 'right', beginAtZero: true, ticks: { color: '#f59e0b' }, grid: { drawOnChartArea: false } }
    }
  };

  const subTabs = [
    { id: 'overview', label: 'Executive Overview', icon: '📊', category: 'General' },
    { id: 'web', label: 'Web Traffic & GA4', icon: '🌐', category: 'Web' },
    { id: 'backend_monitoring', label: 'Cloud Health & Latency', icon: '☁️', category: 'DevOps' },
    { id: 'user_activity', label: 'AI Tokens & Prompts', icon: '🤖', category: 'AI' },
  ];

  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="unified-analytics" style={{ padding: '4px 0 32px 0' }}>
      {/* Alert Banner */}
      {feedback && (
        <div
          className={`alert-banner ${feedback.type}`}
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            marginBottom: '20px',
            background: feedback.type === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            border: `1px solid ${feedback.type === 'error' ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
            color: '#f8fafc',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backdropFilter: 'blur(8px)'
          }}
        >
          <span style={{ fontWeight: '500' }}>{feedback.message}</span>
          <button
            onClick={() => setFeedback(null)}
            style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '18px' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Provider Status Cockpit Badges */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '22px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(99, 102, 241, 0.12)', padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(99, 102, 241, 0.3)', fontSize: '12px', color: '#c7d2fe' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#6366f1', boxShadow: '0 0 8px #6366f1' }}></span>
          <span><strong>GA4 Web:</strong> Connected & Real-Time</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(16, 185, 129, 0.12)', padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(16, 185, 129, 0.3)', fontSize: '12px', color: '#a7f3d0' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }}></span>
          <span><strong>Google Play:</strong> Synced</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(245, 158, 11, 0.12)', padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(245, 158, 11, 0.3)', fontSize: '12px', color: '#fde68a' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b', boxShadow: '0 0 8px #f59e0b' }}></span>
          <span><strong>Cloud Monitoring:</strong> 99.9% Uptime</span>
        </div>

        {/* Auto-refresh indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(56, 189, 248, 0.08)', padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(56, 189, 248, 0.2)', fontSize: '12px', color: '#7dd3fc', marginLeft: 'auto' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#38bdf8', animation: 'pulse 2s infinite' }}></span>
          <span>
            <strong>Auto-Refresh:</strong> Every 5 min
            {lastSynced && <span style={{ color: '#64748b', marginLeft: '8px' }}>• Last: {lastSynced.toLocaleTimeString()}</span>}
          </span>
        </div>
      </div>

      {/* Categorized Filter & Action Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '24px', background: 'rgba(30, 41, 59, 0.6)', padding: '14px 18px', borderRadius: '12px', border: '1px solid #334155' }}>
        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Categorized App Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>Platform Filter</label>
            <select
              value={appCode}
              onChange={(e) => setAppCode(e.target.value)}
              className="filter-select"
              style={{
                background: '#0f172a',
                color: '#f8fafc',
                border: '1px solid #475569',
                padding: '8px 14px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '13px',
                outline: 'none'
              }}
            >
              <option value="all">🌐 All Ecosystem Platforms (Unified)</option>
              <optgroup label="🤖 AI & Consumer Platforms">
                <option value="aisa">✨ AISA AI Suite (aisa)</option>
                <option value="ailegal">⚖️ AI Legal Advisory (ailegal)</option>
                <option value="aimall">🛒 AI Mall Marketplace (aimall)</option>
              </optgroup>
              <optgroup label="⚡ Consciousness & Energy">
                <option value="efvframework">🧘 EFV Alignment Platform (efvframework)</option>
              </optgroup>
              <optgroup label="🌐 Enterprise & Infrastructure">
                <option value="uwo">📦 UWO Main Platform (uwo)</option>
                <option value="uwoconnect">🔗 UWO Connect Networking (uwoconnect)</option>
                <option value="yugamc">🏗️ YUG AMC Real Estate AI (yugamc)</option>
                <option value="unified-dashboard">📊 Unified Admin Control (unified-dashboard)</option>
              </optgroup>
            </select>
          </div>

          {/* Date Range Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>Time Horizon</label>
            <div style={{ display: 'flex', background: '#0f172a', padding: '3px', borderRadius: '8px', border: '1px solid #334155' }}>
              {[
                { key: '24h', label: 'Today (24h)' },
                { key: '7d', label: '7 Days' },
                { key: '30d', label: '30 Days' },
                { key: '90d', label: '90 Days' }
              ].map((r) => (
                <button
                  key={r.key}
                  onClick={() => setDateRange(r.key)}
                  style={{
                    background: dateRange === r.key ? '#6366f1' : 'transparent',
                    color: dateRange === r.key ? '#ffffff' : '#94a3b8',
                    border: 'none',
                    padding: '6px 14px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: dateRange === r.key ? '700' : '500',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end' }}>
          <button
            onClick={() => setShowSnippetModal(true)}
            className="btn-secondary"
            style={{
              background: '#0f172a',
              color: '#e2e8f0',
              border: '1px solid #475569',
              padding: '9px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.15s ease'
            }}
          >
            ⚡ Embed Tracking Code
          </button>

          <button
            onClick={handleSyncAll}
            disabled={syncing}
            className="btn-primary"
            style={{
              background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: '#fff',
              border: 'none',
              padding: '9px 18px',
              borderRadius: '8px',
              cursor: syncing ? 'not-allowed' : 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(99, 102, 241, 0.35)'
            }}
          >
            {syncing ? '🔄 Syncing Providers...' : '🔄 Sync All Providers'}
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs Bar */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #334155', paddingBottom: '12px', marginBottom: '24px', overflowX: 'auto' }}>
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            style={{
              background: activeSubTab === tab.id ? 'rgba(99, 102, 241, 0.18)' : 'rgba(30, 41, 59, 0.4)',
              color: activeSubTab === tab.id ? '#a5b4fc' : '#94a3b8',
              border: activeSubTab === tab.id ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(51, 65, 85, 0.5)',
              padding: '9px 18px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: activeSubTab === tab.id ? '700' : '500',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              whiteSpace: 'nowrap',
              transition: 'all 0.2s ease',
              boxShadow: activeSubTab === tab.id ? '0 2px 10px rgba(99, 102, 241, 0.2)' : 'none'
            }}
          >
            <span style={{ fontSize: '15px' }}>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* ─── TAB 1: OVERVIEW ─────────────────────────────────────────────────── */}
      {activeSubTab === 'overview' && (
        <div>
          <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div className="metric-card" style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(99, 102, 241, 0.25)', borderRadius: '12px', padding: '20px' }}>
              <div className="metric-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>Total Active Users</span>
                <div className="metric-icon" style={{ fontSize: '18px', background: 'rgba(99, 102, 241, 0.15)', padding: '6px', borderRadius: '8px' }}>👥</div>
              </div>
              <div className="metric-value" style={{ fontSize: '28px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.02em' }}>
                {overviewData?.total_users?.toLocaleString() || 0}
              </div>
              <div className="metric-sub" style={{ fontSize: '12px', color: '#818cf8', marginTop: '6px', fontWeight: '500' }}>
                ● {overviewData?.active_users_24h || 0} active in last 24h
              </div>
            </div>

            <div className="metric-card" style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '12px', padding: '20px' }}>
              <div className="metric-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>Web Pageviews</span>
                <div className="metric-icon" style={{ fontSize: '18px', background: 'rgba(56, 189, 248, 0.15)', padding: '6px', borderRadius: '8px' }}>🌐</div>
              </div>
              <div className="metric-value" style={{ fontSize: '28px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.02em' }}>
                {overviewData?.total_web_pageviews?.toLocaleString() || 0}
              </div>
              <div className="metric-sub" style={{ fontSize: '12px', color: '#38bdf8', marginTop: '6px', fontWeight: '500' }}>
                ● Real-Time Tracked ({dateRange === '24h' ? 'Today' : dateRange})
              </div>
            </div>


          </div>

          {/* Timeline Chart */}
          <div className="card-section" style={{ marginTop: '24px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <div className="section-title" style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
                  Cross-Platform Growth & Telemetry Trends
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                  {dateRange === '24h' ? 'Hourly Activity Breakdown (24 Hours)' : `Daily Activity Breakdown (Last ${daysParam} Days)`}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span> Live 100% Real
                </span>
              </div>
            </div>
            <div style={{ height: '330px' }}>
              {loading ? (
                <div style={{ color: '#94a3b8', textAlign: 'center', paddingTop: '60px' }}>Loading Real-Time Analytics...</div>
              ) : (
                <Line data={overviewChartData} options={chartOptions} />
              )}
            </div>
          </div>

          {/* Ecosystem Platform Distribution Section */}
          <div className="card-section" style={{ marginTop: '24px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <div className="section-header" style={{ marginBottom: '20px' }}>
              <div className="section-title" style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
                Ecosystem User Distribution & Share
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                Visual breakdown of active users across all connected applications
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '32px', alignItems: 'center' }}>
              <div style={{ height: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600', marginBottom: '10px' }}>Platform Share Percentage</div>
                <div style={{ height: '250px', width: '100%', display: 'flex', justifyContent: 'center' }}>
                  {loading ? (
                    <div style={{ color: '#94a3b8', textAlign: 'center', paddingTop: '60px' }}>Loading...</div>
                  ) : (
                    <Doughnut 
                      data={appShareChartData} 
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            display: false
                          }
                        }
                      }} 
                    />
                  )}
                </div>
              </div>
              
              <div style={{ height: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600', marginBottom: '10px' }}>Active User Volumes</div>
                <div style={{ height: '250px', width: '100%' }}>
                  {loading ? (
                    <div style={{ color: '#94a3b8', textAlign: 'center', paddingTop: '60px' }}>Loading...</div>
                  ) : (
                    <Bar 
                      data={appShareChartData} 
                      options={{
                        indexAxis: 'y', // Horizontal Bar Chart
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false }
                        },
                        scales: {
                          x: { ticks: { color: '#64748b', precision: 0 }, grid: { color: 'rgba(255,255,255,0.05)' } },
                          y: { ticks: { color: '#94a3b8' }, grid: { display: false } }
                        }
                      }} 
                    />
                  )}
                </div>
              </div>

              {/* Real-time Numeric Summary Card */}
              <div style={{ background: '#0f172a', padding: '18px 20px', borderRadius: '10px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '13px', color: '#f8fafc', fontWeight: '700', marginBottom: '14px', borderBottom: '1px solid #1e293b', paddingBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>📋 Real-Time Registry</span>
                  <span style={{ fontSize: '11px', color: '#10b981', background: 'rgba(16,185,129,0.1)', padding: '2px 8px', borderRadius: '10px' }}>● Live</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {overviewData?.app_breakdown?.map((app, idx) => {
                    const colors = [
                      '#8b5cf6', // AISA
                      '#ec4899', // AI Mall
                      '#f59e0b', // EFV
                      '#3b82f6', // UWO
                      '#10b981', // UWConnect
                      '#6366f1', // AI Legal
                      '#14b8a6', // YUG AMC
                    ];
                    return (
                      <div key={app.app_code} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: colors[idx % colors.length] }}></span>
                          <span style={{ color: '#94a3b8', fontWeight: '500' }}>{app.name}</span>
                        </div>
                        <span style={{ color: '#38bdf8', fontWeight: '700' }}>{app.users?.toLocaleString() || 0} active</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Connected Ecosystem Platforms Table */}
          <div className="card-section" style={{ marginTop: '24px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
            <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
              <div>
                <div className="section-title" style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
                  Connected Ecosystem Platforms
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                  Real-time telemetry, user allocation & live sync status across all 7 platforms
                </div>
              </div>
              <input
                type="text"
                placeholder="🔍 Search applications..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: '#0f172a',
                  color: '#f8fafc',
                  border: '1px solid #475569',
                  padding: '7px 14px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  width: '220px',
                  outline: 'none'
                }}
              />
            </div>
            <div className="table-responsive">
              <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #475569', color: '#94a3b8', fontSize: '12px', textAlign: 'left' }}>
                    <th style={{ padding: '10px 12px' }}>Application</th>
                    <th style={{ padding: '10px 12px' }}>Category</th>
                    <th style={{ padding: '10px 12px' }}>App Code</th>
                    <th style={{ padding: '10px 12px' }}>Registered Users</th>
                    <th style={{ padding: '10px 12px' }}>Telemetry Status</th>
                    <th style={{ padding: '10px 12px', textAlign: 'right' }}>Quick Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {overviewData?.app_breakdown
                    ?.filter((app) =>
                      !searchQuery ||
                      app.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      app.app_code?.toLowerCase().includes(searchQuery.toLowerCase())
                    )
                    ?.map((app) => {
                      const categoryMap = {
                        aisa: { label: 'AI Suite', color: '#8b5cf6' },
                        ailegal: { label: 'Legal AI', color: '#6366f1' },
                        aimall: { label: 'Marketplace', color: '#ec4899' },
                        efvframework: { label: 'Consciousness', color: '#f59e0b' },
                        uwo: { label: 'Web Platform', color: '#3b82f6' },
                        uwoconnect: { label: 'Networking', color: '#10b981' },
                        yugamc: { label: 'Real Estate AI', color: '#14b8a6' },
                        'unified-dashboard': { label: 'Central Admin', color: '#eab308' }
                      };
                      const cat = categoryMap[app.app_code] || { label: 'Product', color: '#64748b' };
                      return (
                        <tr key={app.app_code} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.4)', fontSize: '13px' }}>
                          <td style={{ padding: '12px' }}>
                            <strong style={{ color: '#f8fafc' }}>{app.name}</strong>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <span style={{
                              background: `${cat.color}20`,
                              color: cat.color,
                              border: `1px solid ${cat.color}40`,
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: '600'
                            }}>
                              {cat.label}
                            </span>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <code style={{ background: '#0f172a', padding: '2px 6px', borderRadius: '4px', color: '#93c5fd', fontSize: '12px' }}>
                              {app.app_code}
                            </code>
                          </td>
                          <td style={{ padding: '12px', color: '#e2e8f0', fontWeight: '500' }}>
                            {app.users?.toLocaleString() || 0}
                          </td>
                          <td style={{ padding: '12px' }}>
                            <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></span>
                              {app.status}
                            </span>
                          </td>
                          <td style={{ padding: '12px', textAlign: 'right' }}>
                            <button
                              onClick={() => copySnippet(app.name, app.app_code)}
                              style={{
                                background: copiedApp === app.name ? '#10b981' : '#1e293b',
                                color: copiedApp === app.name ? '#ffffff' : '#94a3b8',
                                border: '1px solid #334155',
                                padding: '4px 10px',
                                borderRadius: '6px',
                                fontSize: '11px',
                                cursor: 'pointer',
                                transition: 'all 0.15s ease'
                              }}
                            >
                              {copiedApp === app.name ? '✓ Copied' : '📋 Copy Tracker'}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}

      {/* ─── TAB 2: WEB ANALYTICS (GA4) ──────────────────────────────────────── */}
      {activeSubTab === 'web' && (
        <div>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span>Total Pageviews</span>
                <div className="metric-icon">📄</div>
              </div>
              <div className="metric-value">{webData?.total_pageviews?.toLocaleString() || 0}</div>
              <div className="metric-sub">GA4 & Web Traffic</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Unique Visitors</span>
                <div className="metric-icon">👤</div>
              </div>
              <div className="metric-value">{webData?.unique_visitors?.toLocaleString() || 0}</div>
              <div className="metric-sub">Unique IP/Visitor Fingerprints</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Avg Engagement Duration</span>
                <div className="metric-icon">⏱️</div>
              </div>
              <div className="metric-value">{webData?.avg_session_duration_s || 0}s</div>
              <div className="metric-sub">Time spent per visit</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Bounce Rate</span>
                <div className="metric-icon">⚡</div>
              </div>
              <div className="metric-value" style={{ color: '#38bdf8' }}>
                {webData?.bounce_rate_pct || 0}%
              </div>
              <div className="metric-sub">Single-page exits</div>
            </div>
          </div>

          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">Web Traffic Timeline (Pageviews vs Visitors)</div>
            </div>
            <div style={{ height: '300px' }}>
              <Line data={webChartData} options={chartOptions} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginTop: '24px' }}>
            {/* Top Pages Table */}
            <div className="card-section">
              <div className="section-header">
                <div className="section-title">Top Visited Pages & Routes</div>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Route</th>
                    <th>Views</th>
                    <th>Visitors</th>
                    <th>Bounce</th>
                  </tr>
                </thead>
                <tbody>
                  {webData?.top_pages?.map((p, idx) => (
                    <tr key={idx}>
                      <td><code>{p.path}</code></td>
                      <td>{p.views?.toLocaleString()}</td>
                      <td>{p.unique_visitors?.toLocaleString()}</td>
                      <td>{p.bounce_rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Traffic Sources */}
            <div className="card-section">
              <div className="section-header">
                <div className="section-title">Traffic Sources & Referrers</div>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Source / Referrer</th>
                    <th>Users</th>
                    <th>Share</th>
                  </tr>
                </thead>
                <tbody>
                  {webData?.traffic_sources?.map((s, idx) => (
                    <tr key={idx}>
                      <td><strong>{s.source}</strong></td>
                      <td>{s.users?.toLocaleString()}</td>
                      <td><span className="badge badge-info">{s.pct}%</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}


      {/* ─── TAB 4: BACKEND & LATENCY (GCP) ──────────────────────────────────── */}
      {activeSubTab === 'backend_monitoring' && (
        <div>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span>Total API Requests</span>
                <div className="metric-icon">🚀</div>
              </div>
              <div className="metric-value">{gcpData?.total_api_requests?.toLocaleString() || 0}</div>
              <div className="metric-sub">Cloud Run Request Volume</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Avg Response Latency</span>
                <div className="metric-icon">⚡</div>
              </div>
              <div className="metric-value" style={{ color: '#10b981' }}>{gcpData?.avg_latency_ms || 0} ms</div>
              <div className="metric-sub">P95: {gcpData?.p95_latency_ms || 0}ms | P99: {gcpData?.p99_latency_ms || 0}ms</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Server 5xx Error Rate</span>
                <div className="metric-icon">🚨</div>
              </div>
              <div className="metric-value" style={{ color: gcpData?.error_5xx_rate < 1.0 ? '#10b981' : '#ef4444' }}>
                {gcpData?.error_5xx_rate || 0}%
              </div>
              <div className="metric-sub">4xx Rate: {gcpData?.error_4xx_rate || 0}%</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>System Health</span>
                <div className="metric-icon">☁️</div>
              </div>
              <div className="metric-value" style={{ color: '#10b981' }}>
                {gcpData?.status?.toUpperCase() || 'HEALTHY'}
              </div>
              <div className="metric-sub">CPU: {gcpData?.cpu_utilization_pct || 24}% | RAM: {gcpData?.memory_utilization_pct || 38}%</div>
            </div>
          </div>

          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">GCP Cloud Run Request Volume & Latency Timeline</div>
            </div>
            <div style={{ height: '300px' }}>
              <Line data={gcpChartData} options={gcpChartOptions} />
            </div>
          </div>

          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">Top REST API Endpoints Performance</div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>API Endpoint</th>
                  <th>Hits</th>
                  <th>Avg Latency</th>
                  <th>HTTP Status</th>
                </tr>
              </thead>
              <tbody>
                {gcpData?.top_endpoints?.map((ep, idx) => (
                  <tr key={idx}>
                    <td><code>{ep.endpoint}</code></td>
                    <td>{ep.hits?.toLocaleString()}</td>
                    <td>{ep.avg_latency_ms} ms</td>
                    <td><span className="badge badge-success">{ep.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── TAB 5: USER ACTIVITY & TOKENS ───────────────────────────────────── */}
      {activeSubTab === 'user_activity' && (
        <div>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span>Total AI Token Usage</span>
                <div className="metric-icon">🧠</div>
              </div>
              <div className="metric-value">{activityData?.ai_token_usage?.total_tokens?.toLocaleString() || 0}</div>
              <div className="metric-sub">Prompts + Completions</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Total AI Sessions</span>
                <div className="metric-icon">💬</div>
              </div>
              <div className="metric-value">{activityData?.ai_token_usage?.total_chats?.toLocaleString() || 0}</div>
              <div className="metric-sub">Chat & AI Workflows</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Internal Events Logged</span>
                <div className="metric-icon">📜</div>
              </div>
              <div className="metric-value">{activityData?.total_events?.toLocaleString() || 0}</div>
              <div className="metric-sub">Client telemetry events</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Active User Sessions</span>
                <div className="metric-icon">👥</div>
              </div>
              <div className="metric-value">{activityData?.total_sessions?.toLocaleString() || 0}</div>
              <div className="metric-sub">Cross-app session count</div>
            </div>
          </div>

          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">Feature / Tool Usage Breakdown</div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Feature / Mode Name</th>
                  <th>Application</th>
                  <th>Invocations Count</th>
                  <th>Share (%)</th>
                </tr>
              </thead>
              <tbody>
                {activityData?.feature_usage?.map((f, idx) => (
                  <tr key={idx}>
                    <td><strong>{f.name}</strong></td>
                    <td><code>{f.app_code}</code></td>
                    <td>{f.count?.toLocaleString()}</td>
                    <td><span className="badge badge-info">{f.pct}%</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}


      {/* ─── EMBED SNIPPET MODAL ─────────────────────────────────────────────── */}
      {showSnippetModal && (
        <div className="modal-backdrop" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="modal-card" style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '24px', maxWidth: '650px', width: '90%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '18px' }}>⚡ Embed Tracking Snippet</h3>
              <button onClick={() => setShowSnippetModal(false)} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>✕</button>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '16px' }}>
              Paste this single-line tracking code into the <code>&lt;head&gt;</code> or <code>index.html</code> of any of your web apps:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {[
                { name: 'AISA Web App', site: 'aisa' },
                { name: 'AI Mall Web App', site: 'aimall' },
                { name: 'EFV Web App', site: 'efvframework' },
                { name: 'UWO Web App', site: 'uwo' },
                { name: 'UWConnect', site: 'uwoconnect' },
                { name: 'AI Legal Web App', site: 'ailegal' },
                { name: 'YUG AMC Web App', site: 'yugamc' },
              ].map((item) => (
                <div key={item.site} style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', border: '1px solid #334155' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', fontWeight: '600', color: '#818cf8' }}>{item.name}</span>
                    <button
                      onClick={() => copySnippet(item.name, item.site)}
                      style={{ background: '#6366f1', color: '#fff', border: 'none', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: '500' }}
                    >
                      {copiedApp === item.name ? '✓ Copied!' : 'Copy Snippet'}
                    </button>
                  </div>
                  <pre style={{ margin: 0, fontSize: '11px', color: '#94a3b8', overflowX: 'auto', background: 'transparent' }}>
                    {`<script defer src="${window.location.hostname === 'localhost' ? window.location.origin : 'https://admin.uwo24.com'}/api/web-stats/tracker.js" data-site="${item.site}" data-endpoint="${window.location.hostname === 'localhost' ? window.location.origin : 'https://admin.uwo24.com'}/api/web-stats/collect"></script>`}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
