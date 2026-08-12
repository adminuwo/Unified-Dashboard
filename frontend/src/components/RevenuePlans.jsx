import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const RevenuePlans = () => {
  const { authFetch } = useAuth();
  const [payments, setPayments] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [payRes, subRes] = await Promise.all([
        authFetch('/api/admin/payments'),
        authFetch('/api/admin/subscriptions'),
      ]);

      if (payRes.ok) setPayments(await payRes.json());
      if (subRes.ok) setSubscriptions(await subRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div>
      {/* Subscriptions Section */}
      <div className="card-section">
        <div className="section-header">
          <div className="section-title">Active Subscriptions</div>
        </div>

        {loading ? (
          <div style={{ color: 'var(--text-muted)' }}>Loading subscriptions...</div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Subscription ID</th>
                  <th>User Email / ID</th>
                  <th>Product</th>
                  <th>Plan</th>
                  <th>Status</th>
                  <th>Provider</th>
                  <th>Created At</th>
                </tr>
              </thead>
              <tbody>
                {subscriptions.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                      No subscriptions recorded.
                    </td>
                  </tr>
                ) : (
                  subscriptions.map((s) => (
                    <tr key={s.id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {s.id}
                      </td>
                      <td>{s.user_email || s.user_id}</td>
                      <td style={{ fontWeight: 600 }}>{s.product_id}</td>
                      <td>{s.plan_id}</td>
                      <td>
                        <span className={`badge badge-${s.status}`}>{s.status.toUpperCase()}</span>
                      </td>
                      <td>{s.provider}</td>
                      <td>{new Date(s.created_at).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Payment Transactions Section */}
      <div className="card-section">
        <div className="section-header">
          <div className="section-title">Payment Transactions (₹ INR)</div>
        </div>

        {loading ? (
          <div style={{ color: 'var(--text-muted)' }}>Loading payments...</div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Payment ID</th>
                  <th>User Email / ID</th>
                  <th>Product / Plan</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Provider ID</th>
                  <th>Created At</th>
                </tr>
              </thead>
              <tbody>
                {payments.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                      No payment transactions recorded yet.
                    </td>
                  </tr>
                ) : (
                  payments.map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {p.id}
                      </td>
                      <td>{p.user_email || p.user_id}</td>
                      <td>{p.product_id} / {p.plan_id}</td>
                      <td style={{ fontWeight: 700, color: 'var(--accent-success)' }}>
                        ₹{p.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })} {p.currency}
                      </td>
                      <td>
                        <span className={`badge badge-${p.status}`}>{p.status.toUpperCase()}</span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                        {p.provider_payment_id || '-'}
                      </td>
                      <td>{new Date(p.created_at).toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
