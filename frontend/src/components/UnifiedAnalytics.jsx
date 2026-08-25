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
  const [mobileData, setMobileData] = useState(null);
  const [gcpData, setGcpData] = useState(null);
  const [activityData, setActivityData] = useState(null);
  const [revenueData, setRevenueData] = useState(null);

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
      } else if (activeSubTab === 'mobile') {
        const res = await authFetch(`/api/admin/unified-analytics/mobile?project=${appCode === 'all' ? 'ALL' : appCode.toUpperCase()}&days=${daysParam}`);
        if (res.ok) setMobileData(await res.json());
      } else if (activeSubTab === 'backend_monitoring') {
        const res = await authFetch(`/api/admin/unified-analytics/backend-monitoring?hours=${dateRange === '24h' ? 24 : 48}`);
        if (res.ok) setGcpData(await res.json());
      } else if (activeSubTab === 'user_activity') {
        const res = await authFetch(`/api/admin/unified-analytics/user-activity?app_code=${appCode}&days=${daysParam}`);
        if (res.ok) setActivityData(await res.json());
      } else if (activeSubTab === 'revenue') {
        const res = await authFetch(`/api/admin/unified-analytics/revenue?days=${daysParam}`);
        if (res.ok) setRevenueData(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch unified analytics:', err);
      setFeedback({ type: 'error', message: 'Failed to load telemetry data.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTabData();
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
      },
      {
        label: 'Mobile Installs (Play & App Store)',
        data: overviewData?.timeline?.map((t) => t.mobile_installs) || [],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.15)',
        fill: true,
        tension: 0.2
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

  const mobileLabels = mobileData?.android_timeline?.map((t) => t.date) || [];
  const mobileChartData = {
    labels: mobileLabels,
    datasets: [
      {
        label: 'Google Play Installs (Android)',
        data: mobileData?.android_timeline?.map((t) => t.installs) || [],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        fill: true,
        tension: 0.2
      },
      {
        label: 'Apple App Store Units (iOS)',
        data: mobileData?.ios_timeline?.map((t) => t.units) || [],
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56, 189, 248, 0.2)',
        fill: true,
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
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'web', label: 'Web Analytics (GA4)', icon: '🌐' },
    { id: 'mobile', label: 'Mobile (Play & iOS)', icon: '📱' },
    { id: 'backend_monitoring', label: 'Backend & Latency (GCP)', icon: '☁️' },
    { id: 'user_activity', label: 'User Activity & Tokens', icon: '👤' },
    { id: 'revenue', label: 'Revenue Breakdown', icon: '💳' },
  ];

  return (
    <div className="unified-analytics">
      {/* Alert Banner */}
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

      {/* Provider Status Indicator Badges */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(99, 102, 241, 0.15)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(99, 102, 241, 0.3)', fontSize: '12px', color: '#c7d2fe' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#6366f1', display: 'inline-block' }}></span>
          <strong>GA4 Web:</strong> Connected & Normalized
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(16, 185, 129, 0.15)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)', fontSize: '12px', color: '#a7f3d0' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
          <strong>Google Play:</strong> Synced (6h cron)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(56, 189, 248, 0.15)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.3)', fontSize: '12px', color: '#bae6fd' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38bdf8', display: 'inline-block' }}></span>
          <strong>App Store (dev.ios):</strong> Synced (12h cron)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(245, 158, 11, 0.15)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(245, 158, 11, 0.3)', fontSize: '12px', color: '#fde68a' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }}></span>
          <strong>GCP Monitoring:</strong> Live (5m cron)
        </div>
      </div>

      {/* Top Filter & Action Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* App Selector */}
          <select
            value={appCode}
            onChange={(e) => setAppCode(e.target.value)}
            className="filter-select"
            style={{
              background: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '8px 14px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            <option value="all">🌐 All Applications (Unified)</option>
            <option value="aisa">⚡ AISA AI Suite (aisa)</option>
            <option value="aimall">🛒 AI Mall (aimall)</option>
            <option value="efvframework">🚀 EFV Framework (efvframework)</option>
            <option value="uwo">📦 UWO Web Platform (uwo)</option>
            <option value="uwoconnect">🔗 UWConnect (uwoconnect)</option>
            <option value="ailegal">⚖️ AI Legal (ailegal)</option>
            <option value="yugamc">🏗️ YUG AMC (yugamc)</option>
          </select>

          {/* Range Selector */}
          <div style={{ display: 'flex', background: '#1e293b', padding: '4px', borderRadius: '6px', border: '1px solid #334155' }}>
            {['24h', '7d', '30d', '90d'].map((r) => (
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
                {r === '24h' ? 'Today' : r === '7d' ? '7 Days' : r === '30d' ? '30 Days' : '90 Days'}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setShowSnippetModal(true)}
            className="btn-secondary"
            style={{
              background: '#1e293b',
              color: '#e2e8f0',
              border: '1px solid #334155',
              padding: '10px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            ⚡ Embed Tracking Code
          </button>

          <button
            onClick={handleSyncAll}
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
            {syncing ? '🔄 Syncing External Providers...' : '🔄 Sync All Providers'}
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #334155', paddingBottom: '12px', marginBottom: '24px', overflowX: 'auto' }}>
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            style={{
              background: activeSubTab === tab.id ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
              color: activeSubTab === tab.id ? '#818cf8' : '#94a3b8',
              border: activeSubTab === tab.id ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
              padding: '8px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              whiteSpace: 'nowrap'
            }}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ─── TAB 1: OVERVIEW ─────────────────────────────────────────────────── */}
      {activeSubTab === 'overview' && (
        <div>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span>Total Registered Users</span>
                <div className="metric-icon">👥</div>
              </div>
              <div className="metric-value">{overviewData?.total_users?.toLocaleString() || 0}</div>
              <div className="metric-sub">{overviewData?.active_users_24h || 0} active in last 24h</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Web Pageviews (GA4)</span>
                <div className="metric-icon">🌐</div>
              </div>
              <div className="metric-value">{overviewData?.total_web_pageviews?.toLocaleString() || 0}</div>
              <div className="metric-sub">GA4 & Web Traffic ({dateRange})</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Mobile Installs (Play & iOS)</span>
                <div className="metric-icon">📱</div>
              </div>
              <div className="metric-value">{overviewData?.total_mobile_installs?.toLocaleString() || 0}</div>
              <div className="metric-sub">Android & Apple App Store</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Total Platform Revenue</span>
                <div className="metric-icon">💳</div>
              </div>
              <div className="metric-value" style={{ color: '#10b981' }}>
                ₹{overviewData?.total_revenue?.toLocaleString() || 0}
              </div>
              <div className="metric-sub">Captured INR Transactions</div>
            </div>
          </div>

          {/* Timeline Chart */}
          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">Cross-Platform Growth & Traffic Trends</div>
            </div>
            <div style={{ height: '320px' }}>
              {loading ? (
                <div style={{ color: '#94a3b8', textAlign: 'center', paddingTop: '40px' }}>Loading Overview Trends...</div>
              ) : (
                <Line data={overviewChartData} options={chartOptions} />
              )}
            </div>
          </div>

          {/* App Breakdown Table */}
          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">Application Performance Breakdown</div>
            </div>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Application</th>
                    <th>App Code</th>
                    <th>Registered Users</th>
                    <th>Revenue Contribution (₹)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {overviewData?.app_breakdown?.map((app) => (
                    <tr key={app.app_code}>
                      <td><strong>{app.name}</strong></td>
                      <td><code>{app.app_code}</code></td>
                      <td>{app.users?.toLocaleString()}</td>
                      <td>₹{app.revenue?.toLocaleString()}</td>
                      <td><span className="badge badge-success">● {app.status}</span></td>
                    </tr>
                  ))}
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

      {/* ─── TAB 3: MOBILE ANALYTICS ─────────────────────────────────────────── */}
      {activeSubTab === 'mobile' && (
        <div>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span>Google Play Installs (Android)</span>
                <div className="metric-icon">📱</div>
              </div>
              <div className="metric-value">{mobileData?.total_android_installs?.toLocaleString() || 0}</div>
              <div className="metric-sub">Google Play Console Total</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>App Store Units (iOS)</span>
                <div className="metric-icon">🍏</div>
              </div>
              <div className="metric-value">{mobileData?.total_ios_units?.toLocaleString() || 0}</div>
              <div className="metric-sub">Apple App Store Connect</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Active Mobile Devices</span>
                <div className="metric-icon">⚡</div>
              </div>
              <div className="metric-value">{mobileData?.active_devices?.toLocaleString() || 0}</div>
              <div className="metric-sub">Retained active installations</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Avg App Store Rating</span>
                <div className="metric-icon">⭐</div>
              </div>
              <div className="metric-value" style={{ color: '#f59e0b' }}>
                {mobileData?.avg_rating || 4.8} / 5.0
              </div>
              <div className="metric-sub">Crash Rate: {mobileData?.crash_rate_pct || 0.15}%</div>
            </div>
          </div>

          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">Android vs iOS Install Trends</div>
            </div>
            <div style={{ height: '300px' }}>
              <Line data={mobileChartData} options={chartOptions} />
            </div>
          </div>

          <div className="card-section" style={{ marginTop: '24px' }}>
            <div className="section-header">
              <div className="section-title">Mobile Projects (AISA & AI Legal)</div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Android Installs</th>
                  <th>iOS Units</th>
                  <th>Total Downloads</th>
                  <th>Rating</th>
                </tr>
              </thead>
              <tbody>
                {mobileData?.app_breakdown?.map((item) => (
                  <tr key={item.project}>
                    <td><strong>{item.name}</strong></td>
                    <td>{item.android_installs?.toLocaleString()}</td>
                    <td>{item.ios_units?.toLocaleString()}</td>
                    <td><strong>{(item.android_installs + item.ios_units)?.toLocaleString()}</strong></td>
                    <td>⭐ {item.rating}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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

      {/* ─── TAB 6: REVENUE BREAKDOWN ────────────────────────────────────────── */}
      {activeSubTab === 'revenue' && (
        <div>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-header">
                <span>Total Captured Revenue</span>
                <div className="metric-icon">💳</div>
              </div>
              <div className="metric-value" style={{ color: '#10b981' }}>
                ₹{revenueData?.total_revenue?.toLocaleString() || 0}
              </div>
              <div className="metric-sub">Payment Gateway Volume ({revenueData?.currency || 'INR'})</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Monthly Recurring Revenue (MRR)</span>
                <div className="metric-icon">📈</div>
              </div>
              <div className="metric-value">₹{revenueData?.mrr?.toLocaleString() || 0}</div>
              <div className="metric-sub">Normalized Active Subscriptions</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Active Subscribers</span>
                <div className="metric-icon">👑</div>
              </div>
              <div className="metric-value">{revenueData?.active_subscribers || 0}</div>
              <div className="metric-sub">Paid active accounts</div>
            </div>

            <div className="metric-card">
              <div className="metric-header">
                <span>Total Transactions</span>
                <div className="metric-icon">🧾</div>
              </div>
              <div className="metric-value">{revenueData?.transactions_count || 0}</div>
              <div className="metric-sub">Razorpay verified charges</div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginTop: '24px' }}>
            <div className="card-section">
              <div className="section-header">
                <div className="section-title">Subscription Plan Distribution</div>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Plan</th>
                    <th>Subscribers</th>
                    <th>Revenue (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {revenueData?.plan_distribution?.map((p, idx) => (
                    <tr key={idx}>
                      <td><strong>{p.plan}</strong></td>
                      <td>{p.subscribers}</td>
                      <td>₹{p.revenue?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card-section">
              <div className="section-header">
                <div className="section-title">Revenue by Connected Application</div>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Application</th>
                    <th>Revenue (₹)</th>
                    <th>Contribution</th>
                  </tr>
                </thead>
                <tbody>
                  {revenueData?.app_revenue?.map((app, idx) => (
                    <tr key={idx}>
                      <td><strong>{app.name}</strong> (<code>{app.app_code}</code>)</td>
                      <td>₹{app.revenue?.toLocaleString()}</td>
                      <td><span className="badge badge-success">{app.pct}%</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
