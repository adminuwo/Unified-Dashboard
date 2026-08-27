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

export const AppDownloadsTab = () => {
  const { authFetch } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [timeseriesData, setTimeseriesData] = useState({
    user_loss: { android: [], ios: [] },
    total_installs: { android: [], ios: [] },
    active_devices: { android: [], ios: [] }
  });
  const [selectedApp, setSelectedApp] = useState('all');
  const [showAndroid, setShowAndroid] = useState(true);
  const [showIos, setShowIos] = useState(true);
  const [loading, setLoading] = useState(true);
  const [lastSynced, setLastSynced] = useState(null);
  const [autoRefreshCountdown, setAutoRefreshCountdown] = useState(300);

  const fetchAnalytics = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const appCodes = selectedApp === 'all' ? 'aisa,ailegal' : selectedApp;
      
      const [overviewRes, lossRes, installsRes, activeRes] = await Promise.all([
        authFetch(`/api/admin/analytics/google-play/overview?app_codes=${appCodes}`),
        authFetch(`/api/admin/analytics/google-play/timeseries?app_codes=${appCodes}&metric=user_loss`),
        authFetch(`/api/admin/analytics/google-play/timeseries?app_codes=${appCodes}&metric=total_installs`),
        authFetch(`/api/admin/analytics/google-play/timeseries?app_codes=${appCodes}&metric=active_devices`)
      ]);

      if (overviewRes.ok) {
        const data = await overviewRes.json();
        setAnalytics(data.data);
      }
      if (lossRes.ok && installsRes.ok && activeRes.ok) {
        const lossData = await lossRes.json();
        const installsData = await installsRes.json();
        const activeData = await activeRes.json();

        setTimeseriesData({
          user_loss: { android: lossData.data?.android || [], ios: lossData.data?.ios || [] },
          total_installs: { android: installsData.data?.android || [], ios: installsData.data?.ios || [] },
          active_devices: { android: activeData.data?.android || [], ios: activeData.data?.ios || [] }
        });
      }
      setLastSynced(new Date());
      setAutoRefreshCountdown(300);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  // Auto-refresh every 5 minutes
  useEffect(() => {
    fetchAnalytics();
    const refreshInterval = setInterval(() => fetchAnalytics(true), 5 * 60 * 1000);
    return () => clearInterval(refreshInterval);
  }, [selectedApp]);

  // Countdown timer display
  useEffect(() => {
    const timer = setInterval(() => {
      setAutoRefreshCountdown(prev => (prev <= 1 ? 300 : prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Safely extract the combined stats from our backend
  const combined = analytics?.combined || {};
  // Use cumulative lifetime total from manual/GCS snapshot; fallback to period sum if not set
  const totalDownloads = (combined.total_user_installs_latest > 0
    ? combined.total_user_installs_latest
    : combined.daily_device_installs) || 0;
  const androidInstalls = (combined.total_user_installs_latest > 0
    ? combined.total_user_installs_latest
    : combined.daily_device_installs) || 0;
  const userInstalls = combined.daily_user_installs || 0;
  const iosDownloads = combined.ios_total_downloads || 0;


  // Chart configs helper that combines Android & iOS in the same chart with legend toggles
  const makeCombinedChart = (seriesObj) => {
    const androidPts = seriesObj?.android || [];
    const iosPts = seriesObj?.ios || [];

    // Union of all dates
    const allDatesSet = new Set([
      ...androidPts.map(p => p.date),
      ...iosPts.map(p => p.date)
    ]);
    const sortedDates = Array.from(allDatesSet).sort();

    const labels = sortedDates.map(dateStr => {
      const d = new Date(dateStr);
      return `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })}`;
    });

    const androidMap = Object.fromEntries(androidPts.map(p => [p.date, p.value]));
    const iosMap = Object.fromEntries(iosPts.map(p => [p.date, p.value]));

    const datasets = [];

    if (showAndroid) {
      datasets.push({
        label: 'Android (Play Store)',
        data: sortedDates.map(d => androidMap[d] ?? 0),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2
      });
    }

    if (showIos) {
      datasets.push({
        label: 'iOS (App Store)',
        data: sortedDates.map(d => iosMap[d] ?? 0),
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56, 189, 248, 0.12)',
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2
      });
    }

    return {
      data: {
        labels,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false // We use custom interactable buttons
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: '#0f172a',
            titleColor: '#94a3b8',
            bodyColor: '#f8fafc',
            borderColor: 'rgba(255,255,255,0.1)',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: '#64748b',
              font: { size: 10 },
              maxTicksLimit: 5
            }
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: {
              color: '#64748b',
              font: { size: 10 },
              maxTicksLimit: 4
            }
          }
        }
      }
    };
  };

  const userLossChart = makeCombinedChart(timeseriesData.user_loss);
  const totalInstallsChart = makeCombinedChart(timeseriesData.total_installs);
  const activeDevicesChart = makeCombinedChart(timeseriesData.active_devices);

  return (
    <div>
      {/* Auto-Sync Status Bar */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.2)',
        borderRadius: '8px', padding: '8px 16px', marginBottom: '16px', flexWrap: 'wrap', gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981', flexShrink: 0 }}></span>
          <span style={{ fontSize: '12px', color: '#34d399', fontWeight: '600' }}>Live Data Feed Active</span>
          {lastSynced && (
            <span style={{ fontSize: '11px', color: '#64748b' }}>
              • Last synced: {lastSynced.toLocaleTimeString()}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            Auto-refresh in <strong style={{ color: '#94a3b8' }}>{Math.floor(autoRefreshCountdown / 60)}:{String(autoRefreshCountdown % 60).padStart(2, '0')}</strong>
          </span>
          <button
            onClick={() => fetchAnalytics(false)}
            disabled={loading}
            style={{
              background: loading ? '#1e293b' : 'rgba(16, 185, 129, 0.15)',
              color: loading ? '#64748b' : '#10b981',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '6px', padding: '4px 12px',
              fontSize: '11px', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '⟳ Refreshing...' : '⟳ Refresh Now'}
          </button>
        </div>
      </div>

      {/* App Code Filter Bar & Platform Toggle Bar */}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        {/* App selector */}
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

        {/* Interactable Platform Legend Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.03)', padding: '4px 8px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', textTransform: 'uppercase', marginRight: '4px' }}>Graph Layers:</span>
          
          <button
            onClick={() => setShowAndroid(!showAndroid)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 12px',
              borderRadius: '8px',
              border: showAndroid ? '1px solid #10b981' : '1px solid transparent',
              backgroundColor: showAndroid ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
              color: showAndroid ? '#34d399' : '#64748b',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: showAndroid ? '#10b981' : '#475569' }} />
            🤖 Android
          </button>

          <button
            onClick={() => setShowIos(!showIos)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 12px',
              borderRadius: '8px',
              border: showIos ? '1px solid #38bdf8' : '1px solid transparent',
              backgroundColor: showIos ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: showIos ? '#38bdf8' : '#64748b',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: showIos ? '#38bdf8' : '#475569' }} />
            🍏 iOS
          </button>
        </div>
      </div>

      {/* Cross-Platform Summary Overview Cards */}
      <div className="metrics-grid" style={{ marginBottom: '24px' }}>
        <div className="metric-card">
          <div className="metric-header">
            <span>Total Combined Downloads</span>
            <div className="metric-icon">📥</div>
          </div>
          <div className="metric-value">{(totalDownloads + iosDownloads).toLocaleString()}</div>
          <div className="metric-sub">Android ({androidInstalls}) + iOS ({iosDownloads})</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Android (Play Store)</span>
            <div className="metric-icon">🤖</div>
          </div>
          <div className="metric-value">{androidInstalls.toLocaleString()}</div>
          <div className="metric-sub">{combined.active_device_installs_latest || 0} active devices • from Play Console</div>
        </div>

        <div className="metric-card" style={{ borderColor: 'rgba(56, 189, 248, 0.4)', background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.1) 0%, rgba(15, 23, 42, 0.6) 100%)' }}>
          <div className="metric-header">
            <span>Apple App Store (iOS)</span>
            <div className="metric-icon">🍏</div>
          </div>
          <div className="metric-value" style={{ color: '#38bdf8' }}>{iosDownloads.toLocaleString()}</div>
          <div className="metric-sub">{combined.ios_first_time_downloads || 0} 1st time • {combined.ios_redownloads || 0} redownloads • {combined.ios_page_views || 0} views</div>
        </div>
      </div>

      {/* Unified Telemetry Trend Graphs Section with Multi-platform curves */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📊 Unified Telemetry Trends
            <span style={{ fontSize: '11px', fontWeight: '600', color: '#10b981', background: 'rgba(16, 185, 129, 0.15)', padding: '2px 8px', borderRadius: '6px' }}>Android</span>
            <span style={{ fontSize: '11px', fontWeight: '600', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.15)', padding: '2px 8px', borderRadius: '6px' }}>iOS</span>
          </h3>
          <span style={{ fontSize: '12px', color: '#64748b' }}>📅 Multi-platform overlay</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {/* Card 1: User loss / Uninstalls */}
          <div className="metric-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>User Loss / Uninstalls</span>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#f8fafc', marginTop: '4px' }}>
                  {combined.avg_daily_user_loss || 0} <span style={{ fontSize: '12px', fontWeight: '500', color: '#94a3b8' }}>Android avg</span>
                </div>
                <div style={{ fontSize: '12px', color: '#38bdf8', marginTop: '2px', fontWeight: '600' }}>
                  Total {combined.daily_user_uninstalls || 0} Android uninstalls • {combined.ios_redownloads || 0} iOS churn
                </div>
              </div>
              <div className="metric-icon" style={{ fontSize: '18px' }}>📉</div>
            </div>
            <div style={{ height: '150px', marginTop: '12px' }}>
              <Line data={userLossChart.data} options={userLossChart.options} />
            </div>
          </div>

          {/* Card 2: Total installs */}
          <div className="metric-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>Total Cumulative Installs</span>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#f8fafc', marginTop: '4px' }}>
                  {(totalDownloads + iosDownloads).toLocaleString()}
                </div>
                <div style={{ fontSize: '12px', color: '#34d399', marginTop: '2px', fontWeight: '600' }}>
                  🤖 {androidInstalls} Play Store • 🍏 {iosDownloads} App Store
                </div>
              </div>
              <div className="metric-icon" style={{ fontSize: '18px' }}>📥</div>
            </div>
            <div style={{ height: '150px', marginTop: '12px' }}>
              <Line data={totalInstallsChart.data} options={totalInstallsChart.options} />
            </div>
          </div>

          {/* Card 3: Active devices & Reach */}
          <div className="metric-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>Active Devices / Reach</span>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#f8fafc', marginTop: '4px' }}>
                  {combined.active_device_installs_latest || 0} <span style={{ fontSize: '12px', fontWeight: '500', color: '#94a3b8' }}>Android Active</span>
                </div>
                <div style={{ fontSize: '12px', color: '#38bdf8', marginTop: '2px', fontWeight: '600' }}>
                  📱 {combined.avg_active_devices || 0} avg devices • {combined.ios_first_time_downloads || 0} 1st time iOS
                </div>
              </div>
              <div className="metric-icon" style={{ fontSize: '18px' }}>📱</div>
            </div>
            <div style={{ height: '150px', marginTop: '12px' }}>
              <Line data={activeDevicesChart.data} options={activeDevicesChart.options} />
            </div>
          </div>
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
            No download events recorded.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Platform / OS</th>
                <th>Total Device Installs</th>
                <th>Active Devices (Latest)</th>
                <th>Average Active Devices</th>
                <th>Uninstalls (User Loss)</th>
                <th>Distribution Share</th>
              </tr>
            </thead>
            <tbody>
              {/* Android Row */}
              <tr>
                <td>
                  <span style={{ fontWeight: '700', color: '#f8fafc', textTransform: 'uppercase' }}>
                    🤖 android (Google Play)
                  </span>
                </td>
                <td>{androidInstalls.toLocaleString()}</td>
                <td style={{ color: '#34d399', fontWeight: '600' }}>{combined.active_device_installs_latest || 0}</td>
                <td style={{ color: '#38bdf8', fontWeight: '600' }}>{combined.avg_active_devices || 0}</td>
                <td style={{ color: '#f87171' }}>{combined.daily_user_uninstalls || 0}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '100px', height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                      <div style={{ width: `${totalDownloads + (combined.ios_total_downloads || 0) > 0 ? Math.round((androidInstalls / (totalDownloads + (combined.ios_total_downloads || 0))) * 100) : 100}%`, height: '100%', backgroundColor: '#10b981' }} />
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: '600', color: '#34d399' }}>
                      {totalDownloads + (combined.ios_total_downloads || 0) > 0 ? Math.round((androidInstalls / (totalDownloads + (combined.ios_total_downloads || 0))) * 100) : 100}%
                    </span>
                  </div>
                </td>
              </tr>

              {/* iOS Row */}
              <tr>
                <td>
                  <span style={{ fontWeight: '700', color: '#f8fafc', textTransform: 'uppercase' }}>
                    🍏 iOS (App Store)
                  </span>
                </td>
                <td>{(combined.ios_total_downloads || 0).toLocaleString()}</td>
                <td style={{ color: '#34d399', fontWeight: '600' }}>{combined.ios_first_time_downloads || 0} (1st time)</td>
                <td style={{ color: '#38bdf8', fontWeight: '600' }}>{combined.ios_redownloads || 0} (redownloads)</td>
                <td style={{ color: '#94a3b8' }}>{combined.ios_page_views || 0} views</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '100px', height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                      <div style={{ width: `${totalDownloads + (combined.ios_total_downloads || 0) > 0 ? Math.round(((combined.ios_total_downloads || 0) / (totalDownloads + (combined.ios_total_downloads || 0))) * 100) : 0}%`, height: '100%', backgroundColor: '#38bdf8' }} />
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: '600', color: '#38bdf8' }}>
                      {totalDownloads + (combined.ios_total_downloads || 0) > 0 ? Math.round(((combined.ios_total_downloads || 0) / (totalDownloads + (combined.ios_total_downloads || 0))) * 100) : 0}%
                    </span>
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
