import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const OverlapAnalytics = () => {
  const { authFetch } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchOverlapData = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/admin/analytics/overlap');
      if (res.ok) {
        const result = await res.json();
        setData(result);
      }
    } catch (err) {
      console.error('Failed to fetch overlap analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverlapData();
  }, []);

  if (loading && !data) {
    return <div style={{ color: 'var(--text-muted)', padding: '20px' }}>Loading application overlap analytics...</div>;
  }

  const { total_users, apps, aisa_app, ailegal_app, overlap, crossover_matrix } = data || {};

  return (
    <div className="overlap-analytics">
      {/* Overview Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span>AISA App Downloads</span>
            <div className="metric-icon">📱</div>
          </div>
          <div className="metric-value">{aisa_app?.users_count || 0}</div>
          <div className="metric-sub">Registered users on AISA</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>AI Legal App Downloads</span>
            <div className="metric-icon">⚖️</div>
          </div>
          <div className="metric-value">{ailegal_app?.users_count || 0}</div>
          <div className="metric-sub">Registered users on AI Legal</div>
        </div>

        <div className="metric-card" style={{ border: '1px solid rgba(16, 185, 129, 0.4)', boxShadow: '0 4px 20px rgba(16, 185, 129, 0.15)' }}>
          <div className="metric-header">
            <span>Joint Downloads (Both Apps)</span>
            <div className="metric-icon">🤝</div>
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-success)' }}>{overlap?.count || 0}</div>
          <div className="metric-sub">Overlap between AISA & AI Legal</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span>Total Core Identities</span>
            <div className="metric-icon">👥</div>
          </div>
          <div className="metric-value">{total_users || 0}</div>
          <div className="metric-sub">Unique platform users</div>
        </div>
      </div>

      {/* Visual Intersect Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
        {/* Visual Venn / Overlap Card */}
        <div className="card-section" style={{ minHeight: '320px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div className="section-header">
            <div className="section-title">AISA vs AI Legal Crossover</div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1, gap: '40px', padding: '20px 0' }}>
            <div style={{ display: 'flex', position: 'relative', width: '280px', height: '160px', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{
                width: '130px',
                height: '130px',
                borderRadius: '50%',
                background: 'rgba(99, 102, 241, 0.25)',
                border: '2px dashed var(--primary)',
                position: 'absolute',
                left: '15px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                boxShadow: '0 0 20px rgba(99, 102, 241, 0.15)'
              }}>
                <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-muted)' }}>AISA</span>
                <span style={{ fontSize: '18px', fontWeight: '800', color: '#fff' }}>{aisa_app?.users_count || 0}</span>
              </div>

              <div style={{
                width: '130px',
                height: '130px',
                borderRadius: '50%',
                background: 'rgba(6, 182, 212, 0.25)',
                border: '2px dashed var(--accent-cyan)',
                position: 'absolute',
                right: '15px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                boxShadow: '0 0 20px rgba(6, 182, 212, 0.15)'
              }}>
                <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-muted)' }}>AI Legal</span>
                <span style={{ fontSize: '18px', fontWeight: '800', color: '#fff' }}>{ailegal_app?.users_count || 0}</span>
              </div>

              {/* Overlap Text Box */}
              <div style={{
                position: 'absolute',
                background: '#0f172a',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                boxShadow: '0 0 15px rgba(16, 185, 129, 0.25)',
                zIndex: 10,
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 'bold', textTransform: 'uppercase' }}>Both</div>
                <div style={{ fontSize: '22px', fontWeight: '900', color: 'var(--accent-success)' }}>{overlap?.count || 0}</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-around', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--primary)' }}>{overlap?.percentage_aisa || 0}%</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>of AISA users use AI Legal</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--accent-cyan)' }}>{overlap?.percentage_legal || 0}%</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>of AI Legal users use AISA</div>
            </div>
          </div>
        </div>

        {/* Apps Distribution Details */}
        <div className="card-section" style={{ minHeight: '320px' }}>
          <div className="section-header">
            <div className="section-title">Unique Users per Standalone App</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '15px' }}>
            {apps?.map(app => {
              const pct = total_users > 0 ? ((app.users_count / total_users) * 100).toFixed(1) : 0;
              const isAisa = app.name.toLowerCase().includes('aisa');
              const isLegal = app.name.toLowerCase().includes('legal');
              const color = isAisa ? 'var(--primary)' : isLegal ? 'var(--accent-cyan)' : 'var(--accent-purple)';
              return (
                <div key={app.id} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '600' }}>
                    <span>{app.name}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{app.users_count} users ({pct}%)</span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${pct}%`,
                      background: color
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Crossover matrix table */}
      <div className="card-section" style={{ marginTop: '24px' }}>
        <div className="section-header">
          <div className="section-title">Cross-Application User Download Overlap Matrix</div>
        </div>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>App Name 1</th>
                <th>App Name 2</th>
                <th>Shared User Count (Joint Downloads)</th>
                <th>Overlap Ratio</th>
              </tr>
            </thead>
            <tbody>
              {crossover_matrix?.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                    No app crossover data available.
                  </td>
                </tr>
              ) : (
                crossover_matrix?.map((row, index) => {
                  const maxCount = Math.max(
                    apps.find(a => a.id === row.app1_id)?.users_count || 1,
                    apps.find(a => a.id === row.app2_id)?.users_count || 1
                  );
                  const overlapRatio = ((row.overlap_count / maxCount) * 100).toFixed(1);
                  return (
                    <tr key={index}>
                      <td style={{ fontWeight: '600' }}>{row.app1_name}</td>
                      <td style={{ fontWeight: '600' }}>{row.app2_name}</td>
                      <td style={{ color: 'var(--accent-success)', fontWeight: 'bold' }}>{row.overlap_count} users</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ width: '80px', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${overlapRatio}%`, background: 'var(--accent-success)' }} />
                          </div>
                          <span>{overlapRatio}% max overlap</span>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
