import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';

export const ChatTrackingTab = () => {
  const { authFetch } = useAuth();
  const [telemetry, setTelemetry] = useState(null);
  const [selectedApp, setSelectedApp] = useState('all');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncNotice, setSyncNotice] = useState(null);
  const [chartType, setChartType] = useState('prompts'); // 'prompts' | 'tokens'
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchTelemetry = async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    try {
      const url = selectedApp === 'all' ? '/api/telemetry/overview' : `/api/telemetry/overview?app_code=${selectedApp}`;
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (err) {
      console.error('Failed to fetch telemetry:', err);
    } finally {
      if (!isBackground) setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, [selectedApp]);

  // Periodic Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTelemetry(true);
    }, 30000);
    return () => clearInterval(interval);
  }, [selectedApp]);

  // Handle Manual Sync
  const handleTriggerSync = async () => {
    setSyncing(true);
    setSyncNotice(null);
    try {
      const res = await authFetch('/api/telemetry/sync', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        setSyncNotice({
          type: 'success',
          msg: `Live Telemetry Sync Successful! Synced ${data.records_synced.toLocaleString()} prompt interactions from connected AI models.`
        });
      } else {
        setSyncNotice({
          type: 'warning',
          msg: data.message || 'Sync completed with warnings.'
        });
      }
      await fetchTelemetry();
    } catch (err) {
      setSyncNotice({ type: 'error', msg: `Sync request failed: ${err.message}` });
    } finally {
      setSyncing(false);
    }
  };

  const formatCompact = (num) => {
    const n = Number(num) || 0;
    if (n >= 1000000) return `${(n / 1000000).toFixed(2)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return n.toLocaleString();
  };

  const timelineData = telemetry?.timeline || [];

  // Filter recent sessions by search
  const filteredSessions = useMemo(() => {
    const list = telemetry?.recent_sessions || [];
    if (!searchQuery.trim()) return list;
    const q = searchQuery.toLowerCase();
    return list.filter(s => 
      (s.session_id && s.session_id.toLowerCase().includes(q)) ||
      (s.model_name && s.model_name.toLowerCase().includes(q)) ||
      (s.preview && s.preview.toLowerCase().includes(q))
    );
  }, [telemetry, searchQuery]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Header & App Controls */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '20px 24px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        boxShadow: '0 12px 30px -5px rgba(0, 0, 0, 0.4)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.02em' }}>
              AI Chat Prompt & LLM Token Telemetry
            </h2>
            <span style={{
              background: 'rgba(99, 102, 241, 0.15)',
              color: '#818cf8',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '20px',
              padding: '3px 10px',
              fontSize: '11px',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px'
            }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', display: 'inline-block', animation: 'pulse 2s infinite' }} />
              Live Ingestion Active
            </span>
          </div>
          <p style={{ margin: '6px 0 0 0', fontSize: '13px', color: '#94a3b8' }}>
            Real-time multi-model prompt consumption, token metrics & session analytics across connected AI apps
          </p>
        </div>

        {/* Sync Button */}
        <button
          onClick={handleTriggerSync}
          disabled={syncing}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: syncing ? '#475569' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
            color: '#ffffff',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '10px',
            padding: '9px 18px',
            fontSize: '13px',
            fontWeight: '700',
            cursor: syncing ? 'not-allowed' : 'pointer',
            boxShadow: '0 4px 14px rgba(99, 102, 241, 0.35)',
            transition: 'all 0.2s ease'
          }}
        >
          <span>{syncing ? '🔄 Syncing Prompts...' : '⚡ Sync Live Telemetry'}</span>
        </button>
      </div>

      {/* Sync Notification Banner */}
      {syncNotice && (
        <div style={{
          padding: '14px 20px',
          borderRadius: '12px',
          background: syncNotice.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${syncNotice.type === 'success' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
          color: syncNotice.type === 'success' ? '#34d399' : '#f87171',
          fontSize: '13px',
          fontWeight: '600',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{syncNotice.type === 'success' ? '✓' : '⚠️'}</span>
            <span>{syncNotice.msg}</span>
          </div>
          <button
            onClick={() => setSyncNotice(null)}
            style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* App Code Filter Bar */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {[
          { id: 'all', label: '🌐 All Applications' },
          { id: 'aisa', label: '🤖 AISA Assistant' },
          { id: 'ailegal', label: '⚖️ AI Legal' },
          { id: 'aiads', label: '📢 AI Ads' },
          { id: 'uwoconnect', label: '🔗 UWO Connect' },
          { id: 'efvframework', label: '📚 EFV Framework' }
        ].map((app) => (
          <button
            key={app.id}
            onClick={() => setSelectedApp(app.id)}
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              border: selectedApp === app.id ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: selectedApp === app.id ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.05)',
              color: selectedApp === app.id ? '#a5b4fc' : '#94a3b8',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: selectedApp === app.id ? '0 2px 8px rgba(99, 102, 241, 0.3)' : 'none'
            }}
          >
            {app.label}
          </button>
        ))}
      </div>

      {/* Executive Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        {/* Total Prompts Logged */}
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Total Prompts Executed
            </span>
            <span style={{ fontSize: '18px' }}>💬</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#f8fafc', margin: '10px 0 6px 0', letterSpacing: '-0.02em' }}>
            {(telemetry?.total_prompts || telemetry?.total_chat_sessions || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '12px', color: '#818cf8', fontWeight: '600' }}>
            Live query & prompt invocations
          </div>
        </div>

        {/* Total Tokens Consumed */}
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(168, 85, 247, 0.25)',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Total Tokens Consumed
            </span>
            <span style={{ fontSize: '18px' }}>🧠</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#c084fc', margin: '10px 0 6px 0', letterSpacing: '-0.02em' }}>
            {(telemetry?.total_tokens || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>
            Input + Output LLM token total
          </div>
        </div>

        {/* Unique Chat Sessions */}
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Active User Sessions
            </span>
            <span style={{ fontSize: '18px' }}>👥</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#34d399', margin: '10px 0 6px 0', letterSpacing: '-0.02em' }}>
            {(telemetry?.total_chat_sessions || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            Unique multi-turn dialogue sessions
          </div>
        </div>

        {/* Average Latency */}
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Average Response Latency
            </span>
            <span style={{ fontSize: '18px' }}>⏱️</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#fbbf24', margin: '10px 0 6px 0', letterSpacing: '-0.02em' }}>
            {telemetry?.avg_latency_ms || 0} ms
          </div>
          <div style={{ fontSize: '12px', color: '#34d399', fontWeight: '600' }}>
            ✓ High throughput execution
          </div>
        </div>
      </div>

      {/* INTERACTIVE PROMPT TIMELINE CHART */}
      {timelineData.length > 0 && (
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '24px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '20px' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '17px', fontWeight: '800', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>📈</span> Daily Prompt Invocations & Token Activity Timeline
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
                Timeseries activity tracking over recent active recording days
              </p>
            </div>

            <div style={{
              display: 'flex',
              background: 'rgba(15, 23, 42, 0.8)',
              borderRadius: '8px',
              padding: '2px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <button
                onClick={() => setChartType('prompts')}
                style={{
                  background: chartType === 'prompts' ? '#6366f1' : 'transparent',
                  color: chartType === 'prompts' ? '#ffffff' : '#94a3b8',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '4px 12px',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
              >
                Prompts Volume
              </button>
              <button
                onClick={() => setChartType('tokens')}
                style={{
                  background: chartType === 'tokens' ? '#6366f1' : 'transparent',
                  color: chartType === 'tokens' ? '#ffffff' : '#94a3b8',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '4px 12px',
                  fontSize: '12px',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
              >
                Tokens Consumed
              </button>
            </div>
          </div>

          {/* SVG Chart */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.7)',
            borderRadius: '12px',
            padding: '20px 16px 12px 16px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
            position: 'relative'
          }}>
            {(() => {
              const svgWidth = 900;
              const svgHeight = 220;
              const padding = { top: 20, right: 30, bottom: 35, left: 60 };
              const width = svgWidth - padding.left - padding.right;
              const height = svgHeight - padding.top - padding.bottom;

              const metricKey = chartType === 'prompts' ? 'prompts' : 'tokens';
              const maxVal = Math.max(...timelineData.map(d => d[metricKey]), 10);
              const yMax = Math.ceil(maxVal * 1.15);

              const points = timelineData.map((d, index) => {
                const x = padding.left + (index / Math.max(timelineData.length - 1, 1)) * width;
                const y = padding.top + height - (d[metricKey] / yMax) * height;
                return { ...d, x, y, index, val: d[metricKey] };
              });

              const linePath = points.reduce((acc, p, idx) => {
                if (idx === 0) return `M ${p.x},${p.y}`;
                const prev = points[idx - 1];
                const cx1 = prev.x + (p.x - prev.x) / 2;
                const cy1 = prev.y;
                const cx2 = prev.x + (p.x - prev.x) / 2;
                const cy2 = p.y;
                return `${acc} C ${cx1},${cy1} ${cx2},${cy2} ${p.x},${p.y}`;
              }, '');

              const areaPath = `${linePath} L ${points[points.length - 1].x},${padding.top + height} L ${points[0].x},${padding.top + height} Z`;
              const totalLabels = Math.min(timelineData.length, 8);
              const labelStep = Math.max(Math.floor(timelineData.length / totalLabels), 1);

              return (
                <div style={{ position: 'relative' }}>
                  <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: '100%', height: '220px', overflow: 'visible' }}>
                    <defs>
                      <linearGradient id="promptAreaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#6366f1" stopOpacity="0.45" />
                        <stop offset="100%" stopColor="#312e81" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Y-Axis Gridlines */}
                    {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
                      const yVal = padding.top + height - ratio * height;
                      const labelVal = yMax * ratio;
                      return (
                        <g key={i}>
                          <line
                            x1={padding.left}
                            y1={yVal}
                            x2={svgWidth - padding.right}
                            y2={yVal}
                            stroke="rgba(255, 255, 255, 0.08)"
                            strokeDasharray={i === 0 ? 'none' : '4 4'}
                          />
                          <text
                            x={padding.left - 10}
                            y={yVal + 4}
                            textAnchor="end"
                            fill="#64748b"
                            fontSize="11"
                            fontWeight="600"
                          >
                            {formatCompact(labelVal)}
                          </text>
                        </g>
                      );
                    })}

                    <path d={areaPath} fill="url(#promptAreaGrad)" />
                    <path d={linePath} fill="none" stroke="#818cf8" strokeWidth="2.5" />

                    {points.map((p, idx) => (
                      <circle
                        key={idx}
                        cx={p.x}
                        cy={p.y}
                        r={hoveredPoint?.index === idx ? 6 : 3.5}
                        fill="#a5b4fc"
                        stroke="#0f172a"
                        strokeWidth="1.5"
                        style={{ cursor: 'pointer' }}
                        onMouseEnter={() => setHoveredPoint(p)}
                      />
                    ))}

                    {/* X-Axis Clean Labels */}
                    {points.map((p, idx) => {
                      if (idx % labelStep !== 0 && idx !== points.length - 1) return null;
                      return (
                        <text
                          key={idx}
                          x={p.x}
                          y={padding.top + height + 20}
                          textAnchor="middle"
                          fill="#94a3b8"
                          fontSize="11"
                          fontWeight="600"
                        >
                          {p.date.slice(5)}
                        </text>
                      );
                    })}
                  </svg>

                  {hoveredPoint && (
                    <div style={{
                      position: 'absolute',
                      top: '12px',
                      left: `${Math.min(Math.max((hoveredPoint.index / Math.max(timelineData.length - 1, 1)) * 100, 15), 85)}%`,
                      transform: 'translateX(-50%)',
                      background: 'rgba(15, 23, 42, 0.95)',
                      border: '1px solid #6366f1',
                      borderRadius: '10px',
                      padding: '10px 14px',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                      pointerEvents: 'none',
                      zIndex: 10,
                      minWidth: '160px'
                    }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '4px' }}>
                        📅 {hoveredPoint.date}
                      </div>
                      <div style={{ fontSize: '14px', fontWeight: '800', color: '#818cf8' }}>
                        Prompts: {hoveredPoint.prompts.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '12px', color: '#c084fc', marginTop: '2px' }}>
                        Tokens: {hoveredPoint.tokens.toLocaleString()}
                      </div>
                      <div style={{ fontSize: '11px', color: '#34d399', marginTop: '2px' }}>
                        Avg Latency: {hoveredPoint.avg_latency} ms
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* AI Model Share Distribution Table */}
      <div style={{
        background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '17px', fontWeight: '800', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🧠</span> AI Model Share & Token Consumption
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
              Execution throughput and volume split across deployed foundation models
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>Loading model analytics...</div>
        ) : !telemetry?.model_share || telemetry.model_share.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#64748b' }}>
            No chat tracking events logged yet for selected filter.
          </div>
        ) : (
          <div className="table-responsive" style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', textAlign: 'left', color: '#94a3b8', fontSize: '12px' }}>
                  <th style={{ padding: '14px 14px' }}>AI Model</th>
                  <th style={{ padding: '14px 14px' }}>Request Count</th>
                  <th style={{ padding: '14px 14px' }}>Total Tokens Consumed</th>
                  <th style={{ padding: '14px 14px' }}>Usage Share</th>
                </tr>
              </thead>
              <tbody>
                {telemetry.model_share.map((m, idx) => {
                  const percentage = telemetry.total_tokens > 0 ? ((m.tokens / telemetry.total_tokens) * 100).toFixed(1) : '0.0';
                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', fontSize: '13px' }}>
                      <td style={{ padding: '14px 14px' }}>
                        <span style={{
                          background: 'rgba(99, 102, 241, 0.15)',
                          color: '#a5b4fc',
                          padding: '4px 10px',
                          borderRadius: '8px',
                          fontWeight: '700',
                          fontSize: '12px',
                          fontFamily: 'monospace'
                        }}>
                          ⚡ {m.model}
                        </span>
                      </td>
                      <td style={{ padding: '14px 14px', fontWeight: '700', color: '#f8fafc' }}>
                        {m.count.toLocaleString()} calls
                      </td>
                      <td style={{ padding: '14px 14px', fontWeight: '700', color: '#c084fc' }}>
                        {m.tokens.toLocaleString()} tokens
                      </td>
                      <td style={{ padding: '14px 14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{ width: '120px', height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                            <div style={{ width: `${percentage}%`, height: '100%', backgroundColor: '#6366f1', borderRadius: '3px' }} />
                          </div>
                          <span style={{ fontSize: '12px', fontWeight: '700', color: '#818cf8' }}>{percentage}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Live Recent Chat / Prompt Stream Table */}
      {filteredSessions.length > 0 && (
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '24px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '17px', fontWeight: '800', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>⚡</span> Real-Time Prompt Stream & Session Logs
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
                Latest prompt interactions recorded live from connected applications
              </p>
            </div>

            <input
              type="text"
              placeholder="Search session ID, model, query..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'rgba(15, 23, 42, 0.85)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '8px',
                padding: '8px 14px',
                color: '#f8fafc',
                fontSize: '12px',
                minWidth: '240px'
              }}
            />
          </div>

          <div className="table-responsive" style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', textAlign: 'left', color: '#94a3b8', fontSize: '12px' }}>
                  <th style={{ padding: '14px 14px' }}>Session / Interaction</th>
                  <th style={{ padding: '14px 14px' }}>Application</th>
                  <th style={{ padding: '14px 14px' }}>Model</th>
                  <th style={{ padding: '14px 14px' }}>Prompt Tokens</th>
                  <th style={{ padding: '14px 14px' }}>Completion Tokens</th>
                  <th style={{ padding: '14px 14px' }}>Total Tokens</th>
                  <th style={{ padding: '14px 14px' }}>Latency</th>
                  <th style={{ padding: '14px 14px' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {filteredSessions.map((s, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', fontSize: '13px' }}>
                    <td style={{ padding: '14px 14px' }}>
                      <div style={{ fontFamily: 'monospace', color: '#818cf8', fontWeight: '600' }}>
                        {s.session_id}
                      </div>
                      {s.preview && (
                        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          "{s.preview}"
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '14px 14px', fontWeight: '700', color: '#f8fafc' }}>
                      {s.app_code}
                    </td>
                    <td style={{ padding: '14px 14px' }}>
                      <span style={{
                        background: 'rgba(99, 102, 241, 0.15)',
                        color: '#a5b4fc',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        fontWeight: '600'
                      }}>
                        {s.model_name}
                      </span>
                    </td>
                    <td style={{ padding: '14px 14px', color: '#cbd5e1' }}>
                      {s.prompt_tokens.toLocaleString()}
                    </td>
                    <td style={{ padding: '14px 14px', color: '#cbd5e1' }}>
                      {s.completion_tokens.toLocaleString()}
                    </td>
                    <td style={{ padding: '14px 14px', fontWeight: '700', color: '#c084fc' }}>
                      {s.total_tokens.toLocaleString()}
                    </td>
                    <td style={{ padding: '14px 14px', color: '#fbbf24', fontWeight: '600' }}>
                      {s.latency_ms} ms
                    </td>
                    <td style={{ padding: '14px 14px', color: '#94a3b8', fontSize: '12px' }}>
                      {s.created_at ? new Date(s.created_at).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
};
