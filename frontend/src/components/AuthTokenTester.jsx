import React, { useState } from 'react';

export const AuthTokenTester = () => {
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [registerName, setRegisterName] = useState('');
  const [registerResult, setRegisterResult] = useState(null);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginResult, setLoginResult] = useState(null);

  const [refreshTokenInput, setRefreshTokenInput] = useState('');
  const [refreshResult, setRefreshResult] = useState(null);

  const [testToken, setTestToken] = useState('');
  const [meResult, setMeResult] = useState(null);
  const [validateResult, setValidateResult] = useState(null);
  const [loadingAction, setLoadingAction] = useState('');

  const API_BASE = '/api';

  // Handle Registration
  const handleRegister = async (e) => {
    e.preventDefault();
    setLoadingAction('register');
    setRegisterResult(null);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: registerEmail,
          password: registerPassword,
          name: registerName || 'User',
        }),
      });
      const data = await res.json();
      setRegisterResult({ status: res.status, data });
    } catch (err) {
      setRegisterResult({ status: 500, data: { error: err.message } });
    } finally {
      setLoadingAction('');
    }
  };

  // Handle Login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoadingAction('login');
    setLoginResult(null);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: loginEmail,
          password: loginPassword,
        }),
      });
      const data = await res.json();
      setLoginResult({ status: res.status, data });
      if (res.ok && data.access_token) {
        setTestToken(data.access_token);
        if (data.refresh_token) {
          setRefreshTokenInput(data.refresh_token);
        }
      }
    } catch (err) {
      setLoginResult({ status: 500, data: { error: err.message } });
    } finally {
      setLoadingAction('');
    }
  };

  // Handle Refresh
  const handleRefresh = async (e) => {
    e.preventDefault();
    setLoadingAction('refresh');
    setRefreshResult(null);
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTokenInput }),
      });
      const data = await res.json();
      setRefreshResult({ status: res.status, data });
      if (res.ok && data.access_token) {
        setTestToken(data.access_token);
        if (data.refresh_token) {
          setRefreshTokenInput(data.refresh_token);
        }
      }
    } catch (err) {
      setRefreshResult({ status: 500, data: { error: err.message } });
    } finally {
      setLoadingAction('');
    }
  };

  // Call /api/auth/me
  const handleCallMe = async () => {
    setLoadingAction('me');
    setMeResult(null);
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${testToken.trim()}`,
        },
      });
      const data = await res.json();
      setMeResult({ status: res.status, data });
    } catch (err) {
      setMeResult({ status: 500, data: { error: err.message } });
    } finally {
      setLoadingAction('');
    }
  };

  // Call /api/auth/validate (Simulates child product integration)
  const handleCallValidate = async () => {
    setLoadingAction('validate');
    setValidateResult(null);
    try {
      const res = await fetch(`${API_BASE}/auth/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: testToken.trim() }),
      });
      const data = await res.json();
      setValidateResult({ status: res.status, data });
    } catch (err) {
      setValidateResult({ status: 500, data: { error: err.message } });
    } finally {
      setLoadingAction('');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ background: '#1e293b', borderRadius: '12px', padding: '20px', color: '#f8fafc' }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '18px', color: '#38bdf8' }}>
          🔒 Unified Identity Auth Service Tester
        </h2>
        <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>
          Test Central Registration, Login, Token Refresh Rotation, and SSO Token Validation for child apps.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* 1. Register Form */}
        <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ color: '#38bdf8', fontSize: '16px', marginTop: 0 }}>1. Register User</h3>
          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <input
              type="text"
              placeholder="Name (e.g. John Doe)"
              value={registerName}
              onChange={(e) => setRegisterName(e.target.value)}
              style={inputStyle}
            />
            <input
              type="email"
              placeholder="Email (e.g. user@domain.com)"
              value={registerEmail}
              onChange={(e) => setRegisterEmail(e.target.value)}
              required
              style={inputStyle}
            />
            <input
              type="password"
              placeholder="Password (min 6 chars)"
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
              required
              style={inputStyle}
            />
            <button type="submit" disabled={loadingAction === 'register'} style={btnStyle}>
              {loadingAction === 'register' ? 'Registering...' : 'Register User'}
            </button>
          </form>
          {registerResult && (
            <pre style={codeBlockStyle}>
              Status: {registerResult.status}{'\n'}
              {JSON.stringify(registerResult.data, null, 2)}
            </pre>
          )}
        </div>

        {/* 2. Login Form */}
        <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ color: '#38bdf8', fontSize: '16px', marginTop: 0 }}>2. Login & Issue Tokens</h3>
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <input
              type="email"
              placeholder="Email"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              required
              style={inputStyle}
            />
            <input
              type="password"
              placeholder="Password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              required
              style={inputStyle}
            />
            <button type="submit" disabled={loadingAction === 'login'} style={btnStyle}>
              {loadingAction === 'login' ? 'Authenticating...' : 'Login'}
            </button>
          </form>
          {loginResult && (
            <pre style={codeBlockStyle}>
              Status: {loginResult.status}{'\n'}
              {JSON.stringify(loginResult.data, null, 2)}
            </pre>
          )}
        </div>

        {/* 3. Refresh Token Panel */}
        <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '12px', padding: '20px' }}>
          <h3 style={{ color: '#38bdf8', fontSize: '16px', marginTop: 0 }}>3. Refresh Token (Rotation)</h3>
          <form onSubmit={handleRefresh} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <input
              type="text"
              placeholder="Refresh Token string"
              value={refreshTokenInput}
              onChange={(e) => setRefreshTokenInput(e.target.value)}
              required
              style={inputStyle}
            />
            <button type="submit" disabled={loadingAction === 'refresh'} style={btnStyle}>
              {loadingAction === 'refresh' ? 'Rotating...' : 'Rotate & Refresh Tokens'}
            </button>
          </form>
          {refreshResult && (
            <pre style={codeBlockStyle}>
              Status: {refreshResult.status}{'\n'}
              {JSON.stringify(refreshResult.data, null, 2)}
            </pre>
          )}
        </div>
      </div>

      {/* 4. Token Tester Panel (Simulating Child Product Integration) */}
      <div style={{ background: '#0f172a', border: '2px solid #38bdf8', borderRadius: '12px', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ color: '#38bdf8', fontSize: '16px', margin: 0 }}>
            ⚡ 4. Child App Integration Tester (Paste JWT Token)
          </h3>
          <span style={{ fontSize: '12px', background: '#0369a1', color: '#e0f2fe', padding: '4px 8px', borderRadius: '6px' }}>
            Simulates Child App (AISA / AI Legal / UWO) Token Validation
          </span>
        </div>

        <textarea
          rows={3}
          placeholder="Paste JWT Access Token here..."
          value={testToken}
          onChange={(e) => setTestToken(e.target.value)}
          style={{ ...inputStyle, width: '100%', fontFamily: 'monospace', fontSize: '13px' }}
        />

        <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
          <button onClick={handleCallMe} disabled={!testToken || loadingAction === 'me'} style={btnStyle}>
            {loadingAction === 'me' ? 'Fetching...' : 'Call GET /api/auth/me'}
          </button>
          <button onClick={handleCallValidate} disabled={!testToken || loadingAction === 'validate'} style={{ ...btnStyle, background: '#10b981' }}>
            {loadingAction === 'validate' ? 'Validating...' : 'Call POST /api/auth/validate'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
          <div>
            <h4 style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 6px 0' }}>GET /api/auth/me Response:</h4>
            <pre style={codeBlockStyle}>
              {meResult ? `Status: ${meResult.status}\n` + JSON.stringify(meResult.data, null, 2) : 'No response yet.'}
            </pre>
          </div>
          <div>
            <h4 style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 6px 0' }}>POST /api/auth/validate Response:</h4>
            <pre style={codeBlockStyle}>
              {validateResult ? `Status: ${validateResult.status}\n` + JSON.stringify(validateResult.data, null, 2) : 'No response yet.'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

const inputStyle = {
  background: '#1e293b',
  border: '1px solid #475569',
  borderRadius: '6px',
  color: '#f8fafc',
  padding: '10px 12px',
  fontSize: '14px',
  outline: 'none',
};

const btnStyle = {
  background: '#0284c7',
  color: '#ffffff',
  border: 'none',
  borderRadius: '6px',
  padding: '10px 16px',
  fontSize: '14px',
  fontWeight: '600',
  cursor: 'pointer',
};

const codeBlockStyle = {
  background: '#020617',
  border: '1px solid #1e293b',
  borderRadius: '6px',
  padding: '12px',
  color: '#38bdf8',
  fontSize: '12px',
  marginTop: '12px',
  overflowX: 'auto',
  maxHeight: '160px',
};
