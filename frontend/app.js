// Admin Dashboard SPA Application Logic
const API_BASE = '/api';
let currentTab = 'overview';
let revenueChart = null;

document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  initDashboard();
  updateSandboxTemplate();
});

// Tab Navigation Logic
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetTab = item.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  currentTab = tabId;

  // Update Nav Active State
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-tab') === tabId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update Panels Active State
  document.querySelectorAll('.tab-panel').forEach(panel => {
    if (panel.id === `panel-${tabId}`) {
      panel.classList.add('active');
    } else {
      panel.classList.remove('active');
    }
  });

  // Update Header Titles
  const titles = {
    overview: { title: 'Dashboard Overview', sub: 'Centralized platform analytics and activity monitoring' },
    applications: { title: 'Application API Keys', sub: 'Manage API keys for standalone connected applications' },
    users: { title: 'Central User Directory', sub: 'Single identity records across all connected products' },
    subscriptions: { title: 'Revenue & Plans', sub: 'Subscriptions and payments handled by Unified Backend' },
    logs: { title: 'Central Logs', sub: 'Real-time application event logs with secret data redaction' },
    sandbox: { title: 'Interactive API Sandbox', sub: 'Test Unified REST APIs live from your browser' }
  };

  if (titles[tabId]) {
    document.getElementById('page-title').innerText = titles[tabId].title;
    document.getElementById('page-subtitle').innerText = titles[tabId].sub;
  }

  refreshCurrentTab();
}

function refreshCurrentTab() {
  switch (currentTab) {
    case 'overview':
      fetchStats();
      break;
    case 'applications':
      fetchAppKeys();
      break;
    case 'users':
      fetchUsers();
      break;
    case 'subscriptions':
      fetchSubscriptions();
      fetchPayments();
      break;
    case 'logs':
      fetchLogs();
      break;
  }
}

// Initial Dashboard Load
function initDashboard() {
  fetchStats();
}

// API Calls
async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/admin/stats`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById('metric-users').innerText = data.total_users;
    document.getElementById('metric-verified').innerText = `${data.verified_users} verified users`;

    document.getElementById('metric-apps').innerText = data.total_applications;
    document.getElementById('metric-active-apps').innerText = `${data.active_applications} active keys`;

    document.getElementById('metric-revenue').innerText = `₹${data.total_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById('metric-subscriptions').innerText = `${data.active_subscriptions} active subscriptions`;

    document.getElementById('metric-logs').innerText = data.total_logs;

    renderChart(data);
  } catch (err) {
    console.error('Failed to fetch stats:', err);
  }
}

function renderChart(stats) {
  const ctx = document.getElementById('revenueChart').getContext('2d');
  if (revenueChart) {
    revenueChart.destroy();
  }

  revenueChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Today'],
      datasets: [{
        label: 'Revenue (₹)',
        data: [0, 0, 0, 0, 0, 0, stats.total_revenue],
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#8b5cf6'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      },
      scales: {
        x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

// Applications Management
async function fetchAppKeys() {
  try {
    const res = await fetch(`${API_BASE}/applications/keys`);
    const tbody = document.getElementById('app-keys-table-body');
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="5" style="color:var(--accent-danger);">Failed to load application keys.</td></tr>`;
      return;
    }
    const keys = await res.json();
    if (keys.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No application keys generated yet. Click "+ Generate Application Key" above.</td></tr>`;
      return;
    }

    tbody.innerHTML = keys.map(k => `
      <tr>
        <td style="font-weight:600;">${escapeHtml(k.application_name)}</td>
        <td style="font-family:monospace; font-size:12px; color:var(--text-muted);">${k.id}</td>
        <td><span class="badge badge-${k.status}">${k.status.toUpperCase()}</span></td>
        <td>${new Date(k.created_at).toLocaleString()}</td>
        <td>
          ${k.status === 'active'
            ? `<button class="btn btn-danger" style="padding:4px 10px; font-size:12px;" onclick="revokeAppKey('${k.id}')">Revoke</button>`
            : '<span style="color:var(--text-dim); font-size:12px;">Revoked</span>'}
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

async function submitCreateKey() {
  const nameInput = document.getElementById('new-app-name');
  const appName = nameInput.value.trim();
  if (!appName) {
    alert('Please enter an application name.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/applications/keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ application_name: appName })
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById('created-key-container').style.display = 'block';
      document.getElementById('created-key-box').innerText = data.api_key;
      document.getElementById('btn-generate-key').style.display = 'none';

      // Auto fill key into sandbox
      document.getElementById('sandbox-app-key').value = data.api_key;

      fetchAppKeys();
      fetchStats();
    } else {
      alert(data.detail || 'Error creating application key.');
    }
  } catch (err) {
    alert('Failed to connect to backend.');
  }
}

async function revokeAppKey(keyId) {
  if (!confirm('Are you sure you want to revoke this application API key? Connected backend applications using this key will immediately lose access.')) {
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/applications/keys/${keyId}`, { method: 'DELETE' });
    if (res.ok) {
      fetchAppKeys();
      fetchStats();
    } else {
      alert('Failed to revoke application key.');
    }
  } catch (err) {
    console.error(err);
  }
}

function openCreateKeyModal() {
  document.getElementById('new-app-name').value = '';
  document.getElementById('created-key-container').style.display = 'none';
  document.getElementById('btn-generate-key').style.display = 'inline-flex';
  document.getElementById('create-key-modal').classList.add('active');
}

function closeCreateKeyModal() {
  document.getElementById('create-key-modal').classList.remove('active');
}

// User Directory
async function fetchUsers() {
  try {
    const res = await fetch(`${API_BASE}/admin/users`);
    const tbody = document.getElementById('users-table-body');
    if (!res.ok) return;
    const users = await res.json();
    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No central users registered yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => `
      <tr>
        <td style="font-family:monospace; font-size:12px; color:var(--text-muted);">${u.id}</td>
        <td style="font-weight:600;">${escapeHtml(u.name)}</td>
        <td>${escapeHtml(u.email)}</td>
        <td><span class="badge badge-${u.is_verified ? 'verified' : 'unverified'}">${u.is_verified ? 'Verified' : 'Unverified'}</span></td>
        <td><span class="badge badge-${u.is_active ? 'active' : 'revoked'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
        <td>${u.subscriptions_count} plan(s)</td>
        <td>${new Date(u.created_at).toLocaleString()}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// Subscriptions & Payments
async function fetchSubscriptions() {
  try {
    const res = await fetch(`${API_BASE}/admin/subscriptions`);
    const tbody = document.getElementById('subscriptions-table-body');
    if (!res.ok) return;
    const subs = await res.json();
    if (subs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No subscriptions active yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = subs.map(s => `
      <tr>
        <td style="font-family:monospace; font-size:12px; color:var(--text-muted);">${s.id}</td>
        <td>${s.user_email || s.user_id}</td>
        <td><span style="font-weight:600;">${escapeHtml(s.product_id)}</span></td>
        <td>${escapeHtml(s.plan_id)}</td>
        <td><span class="badge badge-${s.status}">${s.status.toUpperCase()}</span></td>
        <td>${s.provider}</td>
        <td>${new Date(s.created_at).toLocaleString()}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

async function fetchPayments() {
  try {
    const res = await fetch(`${API_BASE}/admin/payments`);
    const tbody = document.getElementById('payments-table-body');
    if (!res.ok) return;
    const payments = await res.json();
    if (payments.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No payment transactions recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = payments.map(p => `
      <tr>
        <td style="font-family:monospace; font-size:12px; color:var(--text-muted);">${p.id}</td>
        <td>${p.user_email || p.user_id}</td>
        <td>${escapeHtml(p.product_id)} / ${escapeHtml(p.plan_id)}</td>
        <td style="font-weight:700; color:var(--accent-success);">₹${p.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} ${p.currency}</td>
        <td><span class="badge badge-${p.status}">${p.status.toUpperCase()}</span></td>
        <td style="font-family:monospace; font-size:12px;">${p.provider_payment_id || '-'}</td>
        <td>${new Date(p.created_at).toLocaleString()}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// Central Logs
async function fetchLogs() {
  const level = document.getElementById('log-level-filter').value;
  let url = `${API_BASE}/admin/logs`;
  if (level) url += `?level=${level}`;

  try {
    const res = await fetch(url);
    const tbody = document.getElementById('logs-table-body');
    if (!res.ok) return;
    const logs = await res.json();
    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No logs recorded.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => `
      <tr>
        <td style="font-size:12px; color:var(--text-dim);">${new Date(l.created_at).toLocaleString()}</td>
        <td><span class="badge badge-${l.level.toLowerCase()}">${l.level}</span></td>
        <td style="font-weight:600;">${escapeHtml(l.application_name || l.application_id)}</td>
        <td style="font-family:monospace; font-size:12px; color:#38bdf8;">${escapeHtml(l.event)}</td>
        <td>${escapeHtml(l.message)}</td>
        <td style="font-family:monospace; font-size:12px; color:var(--text-muted);">${l.user_id || '-'}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// Sandbox API Tester
function updateSandboxTemplate() {
  const endpoint = document.getElementById('sandbox-endpoint').value;
  const payloadBox = document.getElementById('sandbox-payload');

  const templates = {
    register: JSON.stringify({
      email: "newuser@example.com",
      password: "SecurePassword123!",
      name: "Sandbox User"
    }, null, 2),
    login: JSON.stringify({
      email: "newuser@example.com",
      password: "SecurePassword123!"
    }, null, 2),
    create_payment: JSON.stringify({
      user_id: "<replace_with_user_id>",
      product_id: "product_standalone_app_1",
      plan_id: "plan_pro_monthly",
      amount: 1499.00,
      currency: "INR"
    }, null, 2),
    log: JSON.stringify({
      level: "INFO",
      event: "sandbox_action_executed",
      message: "Testing centralized log API from admin sandbox",
      metadata: { source: "admin_dashboard" }
    }, null, 2)
  };

  payloadBox.value = templates[endpoint] || '{}';
}

async function executeSandboxRequest() {
  const endpoint = document.getElementById('sandbox-endpoint').value;
  const appKey = document.getElementById('sandbox-app-key').value.trim();
  const payloadRaw = document.getElementById('sandbox-payload').value;
  const respBox = document.getElementById('sandbox-response');

  if (!appKey) {
    alert('Please enter an Application API Key (X-Application-Key) or generate one in the Application Keys tab.');
    return;
  }

  let payload;
  try {
    payload = JSON.parse(payloadRaw);
  } catch (e) {
    alert('Invalid JSON in Request Payload.');
    return;
  }

  const endpointUrls = {
    register: '/auth/register',
    login: '/auth/login',
    create_payment: '/payment/create',
    log: '/logs/'
  };

  respBox.innerText = 'Sending request...';

  try {
    const res = await fetch(`${API_BASE}${endpointUrls[endpoint]}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Application-Key': appKey
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    respBox.innerText = `HTTP ${res.status}\n\n${JSON.stringify(data, null, 2)}`;

    // Refresh stats if successful
    if (res.ok) fetchStats();
  } catch (err) {
    respBox.innerText = `Network Error: ${err.message}`;
  }
}

// Utilities
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
