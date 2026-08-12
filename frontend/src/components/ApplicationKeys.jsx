import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const ApplicationKeys = () => {
  const { authFetch } = useAuth();
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [appName, setAppName] = useState('');
  const [createdKey, setCreatedKey] = useState(null);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/applications/keys');
      if (res.ok) {
        const data = await res.json();
        setKeys(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!appName.trim()) return;

    try {
      const res = await authFetch('/api/applications/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ application_name: appName }),
      });

      if (res.ok) {
        const data = await res.json();
        setCreatedKey(data.api_key);
        fetchKeys();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRevokeKey = async (id) => {
    if (!window.confirm('Are you sure you want to revoke this application API key?')) return;
    try {
      const res = await authFetch(`/api/applications/keys/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchKeys();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div className="card-section">
        <div className="section-header">
          <div className="section-title">Registered Application API Keys</div>
          <button className="btn btn-primary" onClick={() => { setCreatedKey(null); setAppName(''); setShowModal(true); }}>
            + Generate Application Key
          </button>
        </div>

        {loading ? (
          <div style={{ color: 'var(--text-muted)' }}>Loading API keys...</div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Application Name</th>
                  <th>Application ID</th>
                  <th>Status</th>
                  <th>Created At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {keys.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                      No application API keys registered yet.
                    </td>
                  </tr>
                ) : (
                  keys.map((k) => (
                    <tr key={k.id}>
                      <td style={{ fontWeight: 600 }}>{k.application_name}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {k.id}
                      </td>
                      <td>
                        <span className={`badge badge-${k.status}`}>{k.status.toUpperCase()}</span>
                      </td>
                      <td>{new Date(k.created_at).toLocaleString()}</td>
                      <td>
                        {k.status === 'active' && (
                          <button
                            className="btn btn-danger"
                            style={{ padding: '4px 10px', fontSize: '12px' }}
                            onClick={() => handleRevokeKey(k.id)}
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Generate Application API Key</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>&times;</button>
            </div>

            {!createdKey ? (
              <form onSubmit={handleCreateKey}>
                <div className="form-group">
                  <label>Application Name</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Standalone E-Commerce App"
                    value={appName}
                    onChange={(e) => setAppName(e.target.value)}
                    required
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Generate Key
                  </button>
                </div>
              </form>
            ) : (
              <div>
                <div className="form-group">
                  <label style={{ color: 'var(--accent-success)', fontWeight: 700 }}>
                    Plaintext Application API Key (Copy Now!)
                  </label>
                  <div className="code-box">{createdKey}</div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="btn btn-primary" onClick={() => setShowModal(false)}>
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
