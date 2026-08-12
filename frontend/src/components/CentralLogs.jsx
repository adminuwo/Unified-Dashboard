import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const CentralLogs = () => {
  const { authFetch } = useAuth();
  const [logs, setLogs] = useState([]);
  const [level, setLevel] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    let url = '/api/admin/logs';
    if (level) url += `?level=${level}`;

    try {
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [level]);

  return (
    <div className="card-section">
      <div className="section-header">
        <div className="section-title">Central Application Audit Logs</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['', 'INFO', 'WARNING', 'ERROR'].map((lvl) => (
            <button
              key={lvl}
              className={`btn ${level === lvl ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '12px' }}
              onClick={() => setLevel(lvl)}
            >
              {lvl || 'ALL'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)' }}>Loading audit logs...</div>
      ) : (
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Application</th>
                <th>Event Code</th>
                <th>Log Message</th>
                <th>User ID</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    No audit logs recorded.
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id}>
                    <td style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                      {new Date(l.created_at).toLocaleString()}
                    </td>
                    <td>
                      <span className={`badge badge-${l.level.toLowerCase()}`}>{l.level}</span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{l.application_name || l.application_id}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: '#38bdf8' }}>
                      {l.event}
                    </td>
                    <td>{l.message}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                      {l.user_id || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
