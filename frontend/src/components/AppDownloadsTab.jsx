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
    user_loss: [],
    total_installs: [],
    active_devices: []
  });
  const [selectedApp, setSelectedApp] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = async () => {
    setLoading(true);
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
          user_loss: lossData.data?.series?.[0]?.points || [],
          total_installs: installsData.data?.series?.[0]?.points || [],
          active_devices: activeData.data?.series?.[0]?.points || []
        });
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

  // Safely extract the combined stats from our backend
  const combined = analytics?.combined || {};
  const totalDownloads = combined.daily_device_installs || 0;
  const androidInstalls = combined.daily_device_installs || 0;
  const userInstalls = combined.daily_user_installs || 0;

  // Chart configs helper
  const makeMiniChart = (dataPoints, label, color, fill = false) => {
    const dates = dataPoints.map(p => {
      const d = new Date(p.date);
      return `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })}`;
    });
    const values = dataPoints.map(p => p.value);

    return {
      data: {
        labels: dates,
        datasets: [{
          label,
          data: values,
          borderColor: color,
          backgroundColor: fill ? `${color}20` : 'transparent',
          fill: fill,
          tension: 0.35,
          pointRadius: 0,
          pointHoverRadius: 4,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
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
              maxTicksLimit: 4
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

  const userLossChart = makeMiniChart(timeseriesData.user_loss, 'User loss', '#38bdf8');
  const totalInstallsChart = makeMiniChart(timeseriesData.total_installs, 'Total installs', '#0284c7', true);
  const activeDevicesChart = makeMiniChart(timeseriesData.active_devices, 'Active devices', '#0ea5e9');

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

      {/* Google Play Monitor KPI Trends Section */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📊 Monitor KPI trends <span style={{ fontSize: '12px', fontWeight: '500', color: '#94a3b8' }}>• Google Play Official Telemetry</span>
          </h3>
          <span style={{ fontSize: '12px', color: '#64748b' }}>📅 Daily Series</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {/* Card 1: User loss */}
          <div className="metric-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>User loss</span>
                <div style={{ fontSize: '26px', fontWeight: '800', color: '#f8fafc', marginTop: '4px' }}>
                  {combined.avg_daily_user_loss || 0} <span style={{ fontSize: '13px', fontWeight: '500', color: '#94a3b8' }}>average</span>
                </div>
                <div style={{ fontSize: '12px', color: '#38bdf8', marginTop: '2px', fontWeight: '600' }}>
                  📉 Total {combined.daily_user_uninstalls || 0} uninstalls recorded
                </div>
              </div>
              <div className="metric-icon" style={{ fontSize: '18px' }}>📉</div>
            </div>
            <div style={{ height: '140px', marginTop: '12px' }}>
              <Line data={userLossChart.data} options={userLossChart.options} />
            </div>
          </div>

          {/* Card 2: Total installs */}
          <div className="metric-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>Total installs</span>
                <div style={{ fontSize: '26px', fontWeight: '800', color: '#f8fafc', marginTop: '4px' }}>
                  {totalDownloads.toLocaleString()}
                </div>
                <div style={{ fontSize: '12px', color: '#34d399', marginTop: '2px', fontWeight: '600' }}>
                  ↑ {userInstalls} unique user accounts
                </div>
              </div>
              <div className="metric-icon" style={{ fontSize: '18px' }}>📥</div>
            </div>
            <div style={{ height: '140px', marginTop: '12px' }}>
              <Line data={totalInstallsChart.data} options={totalInstallsChart.options} />
            </div>
          </div>

          {/* Card 3: Active devices */}
          <div className="metric-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '600' }}>Active devices</span>
                <div style={{ fontSize: '26px', fontWeight: '800', color: '#f8fafc', marginTop: '4px' }}>
                  {combined.avg_active_devices || 0} <span style={{ fontSize: '13px', fontWeight: '500', color: '#94a3b8' }}>average</span>
                </div>
                <div style={{ fontSize: '12px', color: '#34d399', marginTop: '2px', fontWeight: '600' }}>
                  📱 {combined.active_device_installs_latest || 0} latest active devices
                </div>
              </div>
              <div className="metric-icon" style={{ fontSize: '18px' }}>📱</div>
            </div>
            <div style={{ height: '140px', marginTop: '12px' }}>
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
              <tr>
                <td>
                  <span style={{ fontWeight: '700', color: '#f8fafc', textTransform: 'uppercase' }}>
                    📱 android
                  </span>
                </td>
                <td>{androidInstalls.toLocaleString()}</td>
                <td style={{ color: '#34d399', fontWeight: '600' }}>{combined.active_device_installs_latest || 0}</td>
                <td style={{ color: '#38bdf8', fontWeight: '600' }}>{combined.avg_active_devices || 0}</td>
                <td style={{ color: '#f87171' }}>{combined.daily_user_uninstalls || 0}</td>
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
