import React, { useState } from 'react';

export const ApiSandbox = () => {
  const [endpoint, setEndpoint] = useState('register');
  const [appKey, setAppKey] = useState('');
  const [payload, setPayload] = useState(
    JSON.stringify(
      {
        email: 'newuser@example.com',
        password: 'SecurePassword123!',
        name: 'Sandbox User',
      },
      null,
      2
    )
  );
  const [response, setResponse] = useState('');
  const [executing, setExecuting] = useState(false);

  const endpointTemplates = {
    register: JSON.stringify(
      { email: 'newuser@example.com', password: 'SecurePassword123!', name: 'Sandbox User' },
      null,
      2
    ),
    login: JSON.stringify(
      { email: 'newuser@example.com', password: 'SecurePassword123!' },
      null,
      2
    ),
    create_payment: JSON.stringify(
      {
        user_id: '<replace_with_user_id>',
        product_id: 'product_standalone_app_1',
        plan_id: 'plan_pro_monthly',
        amount: 1499.0,
        currency: 'INR',
      },
      null,
      2
    ),
    log: JSON.stringify(
      {
        level: 'INFO',
        event: 'sandbox_action_executed',
        message: 'Testing centralized log API from React admin sandbox',
        metadata: { source: 'react_admin_dashboard' },
      },
      null,
      2
    ),
  };

  const endpointUrls = {
    register: { url: '/api/auth/register', method: 'POST' },
    login: { url: '/api/auth/login', method: 'POST' },
    create_payment: { url: '/api/payment/create', method: 'POST' },
    log: { url: '/api/logs', method: 'POST' },
  };

  const handleEndpointChange = (e) => {
    const ep = e.target.value;
    setEndpoint(ep);
    setPayload(endpointTemplates[ep] || '{}');
  };

  const handleExecute = async () => {
    if (!appKey.trim()) {
      alert('Please enter an Application API Key (X-Application-Key) generated from the Application Keys tab.');
      return;
    }

    let parsedPayload;
    try {
      parsedPayload = JSON.parse(payload);
    } catch (err) {
      alert('Invalid JSON in request payload box.');
      return;
    }

    setExecuting(true);
    setResponse('Sending request to Unified Backend REST API...');

    const epInfo = endpointUrls[endpoint];
    try {
      const res = await fetch(epInfo.url, {
        method: epInfo.method,
        headers: {
          'Content-Type': 'application/json',
          'X-Application-Key': appKey.trim(),
        },
        body: JSON.stringify(parsedPayload),
      });

      const data = await res.json();
      setResponse(JSON.stringify({ status: res.status, ok: res.ok, body: data }, null, 2));
    } catch (err) {
      setResponse(JSON.stringify({ error: err.message }, null, 2));
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="card-section">
      <div className="section-header">
        <div className="section-title">Standalone App API Sandbox Tester</div>
      </div>

      <div className="form-group">
        <label>Select Target REST API Endpoint</label>
        <select className="form-control" value={endpoint} onChange={handleEndpointChange}>
          <option value="register">POST /api/auth/register (User Registration)</option>
          <option value="login">POST /api/auth/login (User Authentication / JWT)</option>
          <option value="create_payment">POST /api/payment/create (Payment Intent - ₹ INR)</option>
          <option value="log">POST /api/logs (Central Audit Log Submission)</option>
        </select>
      </div>

      <div className="form-group">
        <label>Application API Key (X-Application-Key Header)</label>
        <input
          type="text"
          className="form-control"
          style={{ fontFamily: 'var(--font-mono)' }}
          placeholder="Paste generated API key (e.g. key_abc123...)"
          value={appKey}
          onChange={(e) => setAppKey(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>JSON Request Body</label>
        <textarea
          className="form-control"
          rows={7}
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
        />
      </div>

      <button className="btn btn-primary" onClick={handleExecute} disabled={executing}>
        {executing ? 'Executing Request...' : '⚡ Send Test Request'}
      </button>

      {response && (
        <div className="form-group" style={{ marginTop: '24px' }}>
          <label style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>API Response Output</label>
          <pre className="code-box" style={{ color: '#f8fafc', whiteSpace: 'pre-wrap' }}>
            {response}
          </pre>
        </div>
      )}
    </div>
  );
};
