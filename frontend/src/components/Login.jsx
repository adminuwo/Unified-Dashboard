import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showForgotHelp, setShowForgotHelp] = useState(false);
  const { login, loading, error } = useAuth();


  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) return;
    await login(username, password);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-brand-icon">⚡</div>
          <h2>Unified Platform Admin</h2>
          <p>Sign in with your master admin account</p>
        </div>

        {error && (
          <div className="alert-danger">
            <span>⚠️</span> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Master Admin Username / Email</label>
            <input
              type="text"
              className="form-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter admin username or email"
              required
            />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ margin: 0 }}>Password</label>
              <button
                type="button"
                onClick={() => setShowForgotHelp(true)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#38bdf8',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline'
                }}
              >
                Forgot password?
              </button>
            </div>
            <input
              type="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '8px', padding: '12px' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In to Dashboard'}
          </button>
        </form>

        {showForgotHelp && (
          <div
            style={{
              marginTop: '20px',
              padding: '16px',
              background: '#0f172a',
              border: '1px solid #38bdf8',
              borderRadius: '12px',
              textAlign: 'left',
              fontSize: '13px',
              color: '#e2e8f0',
              lineHeight: '1.5'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <strong style={{ color: '#38bdf8' }}>🔐 Master Admin Password Recovery</strong>
              <button
                type="button"
                onClick={() => setShowForgotHelp(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '16px',
                  lineHeight: 1
                }}
              >
                ×
              </button>
            </div>
            <p style={{ margin: '0 0 8px 0' }}>
              For infrastructure security, Master Admin passwords can be recovered or reset via the CLI utility on the host server:
            </p>
            <code
              style={{
                display: 'block',
                background: '#020617',
                padding: '8px 10px',
                borderRadius: '6px',
                color: '#38bdf8',
                fontSize: '12px',
                marginBottom: '8px',
                fontFamily: 'monospace'
              }}
            >
              python create_super_admin.py
            </code>
            <p style={{ margin: 0, fontSize: '11px', color: '#94a3b8' }}>
              Tip: Developer accounts support default admin credentials in local/test environments.
            </p>
          </div>
        )}
      </div>
    </div>

  );
};
