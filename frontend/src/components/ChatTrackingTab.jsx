import React, { useEffect, useState, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';

// Application Configurations (Distinct Apps across Web & Mobile)
const APP_CONFIGS = {
  ailegal: {
    id: 'ailegal',
    name: 'AI Legal',
    platform: 'Web & Mobile App',
    icon: '⚖️',
    color: '#6366f1',
    metric1Title: 'Total Consultations & Cases',
    metric1Subtitle: 'Live legal inquiries, drafting & research',
    metric3Title: 'Active Advocates & Clients',
    metric3Subtitle: 'Identified legal users with interaction logs',
    userSectionTitle: 'AI Legal — Advocate & User Case Consultations',
    userSectionSubtitle: 'Real-time inspection of legal inquiries, drafting sessions, client matters, and statutory issue analysis across Web & Mobile App.',
    itemUnit: 'Consultation',
    itemUnitPlural: 'Consultations',
    searchPlaceholder: 'Search by advocate name, email, client name, or case topic...'
  },
  aisa: {
    id: 'aisa',
    name: 'AISA Assistant',
    platform: 'Web & Mobile App',
    icon: '🤖',
    color: '#38bdf8',
    metric1Title: 'Total Conversations & Prompts',
    metric1Subtitle: 'Conversational AI queries & multimodal workflows',
    metric3Title: 'Active AI Users',
    metric3Subtitle: 'Identified users with conversation histories',
    userSectionTitle: 'AISA Assistant — User Conversation & Query Logs',
    userSectionSubtitle: 'Real-time inspection of conversational prompts, AI workflows, and live chat sessions across Web & Mobile App.',
    itemUnit: 'Prompt',
    itemUnitPlural: 'Prompts',
    searchPlaceholder: 'Search by user name, email, query keyword, or session ID...'
  },
  aiads: {
    id: 'aiads',
    name: 'AI Ads',
    platform: 'Web Platform',
    icon: '📢',
    color: '#ec4899',
    metric1Title: 'Ad Copy & Creative Sessions',
    metric1Subtitle: 'Campaign prompts & variations generated',
    metric3Title: 'Active Marketers',
    metric3Subtitle: 'Marketing teams & creators',
    userSectionTitle: 'AI Ads — Creative Generation Logs',
    userSectionSubtitle: 'Real-time tracking of marketing copy, ad variations, and headline generation across the Web Platform.',
    itemUnit: 'Creative Session',
    itemUnitPlural: 'Creative Sessions',
    searchPlaceholder: 'Search by marketer name, email, or ad topic...'
  },
  efvframework: {
    id: 'efvframework',
    name: 'EFV Framework',
    platform: 'Web Platform',
    icon: '📚',
    color: '#10b981',
    metric1Title: 'Knowledge & RAG Inquiries',
    metric1Subtitle: 'E-book queries & reading telemetry',
    metric3Title: 'Active Readers & Students',
    metric3Subtitle: 'Course students & digital readers',
    userSectionTitle: 'EFV Framework — Reader & Student Inquiries',
    userSectionSubtitle: 'Real-time semantic e-book questions, audiobook interactions, and knowledge retrieval across the Web Platform.',
    itemUnit: 'Query',
    itemUnitPlural: 'Queries',
    searchPlaceholder: 'Search by reader name, email, or knowledge topic...'
  }
};

const APPS_LIST = [
  { id: 'ailegal', label: '⚖️ AI Legal (Web & App)' },
  { id: 'aisa', label: '🤖 AISA Assistant (Web & App)' },
  { id: 'aiads', label: '📢 AI Ads (Web)' },
  { id: 'efvframework', label: '📚 EFV Framework (Web)' }
];

export const ChatTrackingTab = () => {
  const { authFetch } = useAuth();
  const [telemetry, setTelemetry] = useState(null);
  const [selectedApp, setSelectedApp] = useState('ailegal'); // Defaults cleanly to AI Legal
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncNotice, setSyncNotice] = useState(null);
  const [chartType, setChartType] = useState('prompts'); // 'prompts' | 'tokens'
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [expandedUser, setExpandedUser] = useState(null);
  const [activeModalCase, setActiveModalCase] = useState(null);

  // Lightweight Pagination States
  const [userPage, setUserPage] = useState(1);
  const USERS_PER_PAGE = 10;
  const [sessionPage, setSessionPage] = useState(1);
  const SESSIONS_PER_PAGE = 12;

  const currentConfig = APP_CONFIGS[selectedApp] || APP_CONFIGS.ailegal;

  const fetchTelemetry = async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    try {
      const res = await authFetch(`/api/telemetry/overview?app_code=${selectedApp}`);
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
    setUserPage(1);
    setSessionPage(1);
    setSelectedCategory('ALL');
    setSearchQuery('');
    setExpandedUser(null);
    fetchTelemetry();
  }, [selectedApp]);

  // Periodic Auto-refresh every 45 seconds (Lightweight)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchTelemetry(true);
    }, 45000);
    return () => clearInterval(interval);
  }, [selectedApp]);

  // Handle Manual Sync from Connected Databases
  const handleTriggerSync = async () => {
    setSyncing(true);
    setSyncNotice(null);
    try {
      const res = await authFetch('/api/telemetry/sync', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        setSyncNotice({
          type: 'success',
          msg: `Live Real-Time Sync Successful! Ingested ${data.records_synced.toLocaleString()} prompt interactions from Atlas.`
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

  const formatLatency = (ms) => {
    const n = Number(ms) || 0;
    if (n >= 1000) {
      return `${(n / 1000).toFixed(2)} s`;
    }
    return `${Math.round(n)} ms`;
  };

  const timelineData = telemetry?.timeline || [];
  const usersTrackingList = telemetry?.users_tracking || [];
  const chatCategories = telemetry?.chat_categories || [];

  // Filter users by search and category
  const filteredUsers = useMemo(() => {
    let list = usersTrackingList;
    if (selectedCategory !== 'ALL') {
      list = list.filter(u => u.chat_types && u.chat_types.includes(selectedCategory));
    }
    if (!searchQuery.trim()) return list;
    const q = searchQuery.toLowerCase();
    return list.filter(u => 
      (u.name && u.name.toLowerCase().includes(q)) ||
      (u.email && u.email.toLowerCase().includes(q)) ||
      (u.user_id && u.user_id.toLowerCase().includes(q)) ||
      (u.cases && u.cases.some(c => 
        (c.title && c.title.toLowerCase().includes(q)) ||
        (c.summary && c.summary.toLowerCase().includes(q)) ||
        (c.client_name && c.client_name.toLowerCase().includes(q)) ||
        (c.chat_type && c.chat_type.toLowerCase().includes(q))
      ))
    );
  }, [usersTrackingList, selectedCategory, searchQuery]);

  // Paginated users for lightweight DOM rendering
  const totalUserPages = Math.ceil(filteredUsers.length / USERS_PER_PAGE) || 1;
  const paginatedUsers = useMemo(() => {
    const start = (userPage - 1) * USERS_PER_PAGE;
    return filteredUsers.slice(start, start + USERS_PER_PAGE);
  }, [filteredUsers, userPage]);

  // Filter and paginate recent sessions
  const filteredSessions = useMemo(() => {
    const list = telemetry?.recent_sessions || [];
    if (!searchQuery.trim()) return list;
    const q = searchQuery.toLowerCase();
    return list.filter(s => 
      (s.session_id && s.session_id.toLowerCase().includes(q)) ||
      (s.model_name && s.model_name.toLowerCase().includes(q)) ||
      (s.user_name && s.user_name.toLowerCase().includes(q)) ||
      (s.user_email && s.user_email.toLowerCase().includes(q)) ||
      (s.chat_type && s.chat_type.toLowerCase().includes(q)) ||
      (s.preview && s.preview.toLowerCase().includes(q))
    );
  }, [telemetry, searchQuery]);

  const totalSessionPages = Math.ceil(filteredSessions.length / SESSIONS_PER_PAGE) || 1;
  const paginatedSessions = useMemo(() => {
    const start = (sessionPage - 1) * SESSIONS_PER_PAGE;
    return filteredSessions.slice(start, start + SESSIONS_PER_PAGE);
  }, [filteredSessions, sessionPage]);

  // Category Badge Colors & Icons
  const getCategoryColor = (cat) => {
    if (!cat) return { bg: 'rgba(148, 163, 184, 0.15)', text: '#94a3b8', border: 'rgba(148, 163, 184, 0.3)', icon: '🏷️' };
    const c = cat.toLowerCase();
    if (c.includes('cheque') || c.includes('debt')) {
      return { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: 'rgba(239, 68, 68, 0.35)', icon: '💳' };
    } else if (c.includes('employment') || c.includes('salary')) {
      return { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: 'rgba(245, 158, 11, 0.35)', icon: '💼' };
    } else if (c.includes('divorce') || c.includes('matrimonial')) {
      return { bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', border: 'rgba(236, 72, 153, 0.35)', icon: '💍' };
    } else if (c.includes('property') || c.includes('estate') || c.includes('tenant')) {
      return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: 'rgba(16, 185, 129, 0.35)', icon: '🏢' };
    } else if (c.includes('criminal') || c.includes('appeal') || c.includes('fir')) {
      return { bg: 'rgba(220, 38, 38, 0.18)', text: '#fca5a5', border: 'rgba(220, 38, 38, 0.4)', icon: '⚖️' };
    } else if (c.includes('contract') || c.includes('nda')) {
      return { bg: 'rgba(14, 165, 233, 0.15)', text: '#38bdf8', border: 'rgba(14, 165, 233, 0.35)', icon: '📜' };
    } else if (c.includes('pleading') || c.includes('draft')) {
      return { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc', border: 'rgba(168, 85, 247, 0.35)', icon: '📂' };
    } else if (c.includes('cashflow') || c.includes('financial')) {
      return { bg: 'rgba(34, 197, 94, 0.15)', text: '#4ade80', border: 'rgba(34, 197, 94, 0.35)', icon: '💰' };
    } else if (c.includes('ad') || c.includes('creative')) {
      return { bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', border: 'rgba(236, 72, 153, 0.35)', icon: '📢' };
    }
    return { bg: 'rgba(99, 102, 241, 0.15)', text: '#a5b4fc', border: 'rgba(99, 102, 241, 0.35)', icon: '💬' };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      
      {/* Top Application Filter Bar (No 'All Applications' option - Clean App Selection) */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '18px 24px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        boxShadow: '0 12px 30px -5px rgba(0, 0, 0, 0.4)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>{currentConfig.icon}</span> {currentConfig.name} <span style={{ fontSize: '13px', fontWeight: '600', color: '#94a3b8' }}>({currentConfig.platform})</span>
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
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', display: 'inline-block' }} />
              Live Connected Sync
            </span>
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#94a3b8' }}>
            Real-time tracking of AI chat sessions, prompt token consumption & user interaction history.
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
          <span>{syncing ? '🔄 Refreshing...' : '⚡ Sync Live Real-Time Data'}</span>
        </button>
      </div>

      {/* Sync Notification Banner */}
      {syncNotice && (
        <div style={{
          padding: '12px 18px',
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

      {/* Application Switcher Pills (Web & App Dedicated Tabs) */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        {APPS_LIST.map((app) => {
          const isSelected = selectedApp === app.id;
          return (
            <button
              key={app.id}
              onClick={() => setSelectedApp(app.id)}
              style={{
                padding: '9px 18px',
                borderRadius: '24px',
                border: isSelected ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.1)',
                backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgba(30, 41, 59, 0.6)',
                color: isSelected ? '#ffffff' : '#94a3b8',
                fontWeight: '700',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isSelected ? '0 2px 12px rgba(99, 102, 241, 0.35)' : 'none',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>{app.label}</span>
            </button>
          );
        })}
      </div>

      {/* Executive Metric Cards (Dynamic Context Per App) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        {/* Metric 1: Total Prompts / Cases */}
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              {currentConfig.metric1Title}
            </span>
            <span style={{ fontSize: '18px' }}>💬</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#f8fafc', margin: '10px 0 6px 0', letterSpacing: '-0.02em' }}>
            {(telemetry?.total_prompts || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '12px', color: '#818cf8', fontWeight: '600' }}>
            {currentConfig.metric1Subtitle}
          </div>
        </div>

        {/* Metric 2: Total Tokens Consumed */}
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

        {/* Metric 3: Active Identified Users */}
        <div style={{
          background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.25)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              {currentConfig.metric3Title}
            </span>
            <span style={{ fontSize: '18px' }}>👥</span>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#34d399', margin: '10px 0 6px 0', letterSpacing: '-0.02em' }}>
            {(usersTrackingList.length || telemetry?.total_chat_sessions || 0).toLocaleString()}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            {currentConfig.metric3Subtitle}
          </div>
        </div>

        {/* Metric 4: Average Latency */}
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
            {formatLatency(telemetry?.avg_latency_ms)}
          </div>
          <div style={{ fontSize: '12px', color: '#34d399', fontWeight: '600' }}>
            ✓ High throughput execution
          </div>
        </div>
      </div>

      {/* USER INTERACTION & SESSION SECTION */}
      <div style={{
        background: 'linear-gradient(145deg, #1e293b 0%, #0f172a 100%)',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.35)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '20px' }}>📋</span>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.01em' }}>
                {currentConfig.userSectionTitle}
              </h3>
              <span style={{
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#818cf8',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                borderRadius: '6px',
                padding: '2px 8px',
                fontSize: '11px',
                fontWeight: '700'
              }}>
                {filteredUsers.length} Users Active
              </span>
            </div>
            <p style={{ margin: '6px 0 0 0', fontSize: '13px', color: '#94a3b8' }}>
              {currentConfig.userSectionSubtitle}
            </p>
          </div>

          {/* Search Box */}
          <input
            type="text"
            placeholder={currentConfig.searchPlaceholder}
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setUserPage(1);
            }}
            style={{
              background: 'rgba(15, 23, 42, 0.85)',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              borderRadius: '8px',
              padding: '10px 16px',
              color: '#f8fafc',
              fontSize: '13px',
              minWidth: '280px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
            }}
          />
        </div>

        {/* Category Filter Pills */}
        {chatCategories.length > 0 && (
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <button
              onClick={() => {
                setSelectedCategory('ALL');
                setUserPage(1);
              }}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer',
                border: selectedCategory === 'ALL' ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.1)',
                background: selectedCategory === 'ALL' ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                color: selectedCategory === 'ALL' ? '#a5b4fc' : '#94a3b8'
              }}
            >
              🌐 All Categories ({telemetry?.total_prompts || 0})
            </button>
            {chatCategories.map((c, i) => {
              const col = getCategoryColor(c.category);
              const isSelected = selectedCategory === c.category;
              return (
                <button
                  key={i}
                  onClick={() => {
                    setSelectedCategory(isSelected ? 'ALL' : c.category);
                    setUserPage(1);
                  }}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    border: isSelected ? `1px solid ${col.text}` : `1px solid ${col.border}`,
                    background: isSelected ? col.bg : 'rgba(15, 23, 42, 0.6)',
                    color: isSelected ? '#ffffff' : col.text,
                    boxShadow: isSelected ? `0 0 10px ${col.bg}` : 'none'
                  }}
                >
                  <span>{col.icon || '🏷️'}</span>
                  <span>{c.category}</span>
                  <span style={{
                    background: 'rgba(255, 255, 255, 0.15)',
                    padding: '1px 6px',
                    borderRadius: '10px',
                    fontSize: '10px',
                    color: '#f8fafc'
                  }}>
                    {c.count}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* User Interaction Cards (Paginated for Lightweight Performance) */}
        {loading ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>🔄</div>
            <div>Loading user activity logs...</div>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#64748b' }}>
            No user records found for {currentConfig.name}.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {paginatedUsers.map((user) => {
              const isExpanded = expandedUser === user.user_id;
              const displayName = user.name || `User ${user.user_id.slice(0, 8)}`;
              const initials = displayName.split(' ').filter(Boolean).map(w => w[0]).join('').slice(0, 2).toUpperCase() || 'U';

              return (
                <div
                  key={user.user_id}
                  style={{
                    background: 'rgba(15, 23, 42, 0.75)',
                    border: isExpanded ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    transition: 'all 0.2s ease',
                    boxShadow: isExpanded ? '0 8px 24px rgba(99, 102, 241, 0.15)' : 'none'
                  }}
                >
                  {/* User Summary Header */}
                  <div
                    onClick={() => setExpandedUser(isExpanded ? null : user.user_id)}
                    style={{
                      padding: '14px 18px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer',
                      flexWrap: 'wrap',
                      gap: '14px',
                      userSelect: 'none'
                    }}
                  >
                    {/* User Identity */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
                        background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                        color: '#ffffff',
                        fontWeight: '800',
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
                      }}>
                        {initials}
                      </div>
                      <div>
                        <div style={{ fontSize: '15px', fontWeight: '800', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span>{displayName}</span>
                          <span style={{
                            background: 'rgba(16, 185, 129, 0.15)',
                            color: '#34d399',
                            fontSize: '10px',
                            fontWeight: '700',
                            padding: '2px 6px',
                            borderRadius: '4px'
                          }}>
                            ● Active
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px', fontFamily: 'monospace' }}>
                          {user.email || 'user@app.com'} • ID: {user.user_id.slice(0, 10)}...
                        </div>
                      </div>
                    </div>

                    {/* Interaction Category Badges */}
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center', maxWidth: '480px' }}>
                      {(user.chat_types || []).map((t, idx) => {
                        const style = getCategoryColor(t);
                        return (
                          <span
                            key={idx}
                            style={{
                              background: style.bg,
                              color: style.text,
                              border: `1px solid ${style.border}`,
                              borderRadius: '6px',
                              padding: '2px 8px',
                              fontSize: '11px',
                              fontWeight: '600',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            <span>{style.icon || '🏷️'}</span>
                            <span>{t}</span>
                          </span>
                        );
                      })}
                    </div>

                    {/* Stats & Toggle */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '14px', fontWeight: '800', color: '#818cf8' }}>
                          {user.total_cases} {user.total_cases === 1 ? currentConfig.itemUnit : currentConfig.itemUnitPlural}
                        </div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>
                          {user.total_tokens ? `${user.total_tokens.toLocaleString()} tokens` : 'Active'}
                        </div>
                      </div>
                      <span style={{
                        fontSize: '16px',
                        color: '#94a3b8',
                        transform: isExpanded ? 'rotate(180deg)' : 'none',
                        transition: 'transform 0.2s ease'
                      }}>
                        ▼
                      </span>
                    </div>
                  </div>

                  {/* Expanded Consultations / Prompt History */}
                  {isExpanded && (
                    <div style={{
                      padding: '0 18px 18px 18px',
                      borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                      background: 'rgba(10, 15, 30, 0.6)'
                    }}>
                      <div style={{
                        fontSize: '12px',
                        fontWeight: '700',
                        color: '#818cf8',
                        margin: '14px 0 10px 0',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <span>📋 Interaction Records for {displayName}</span>
                        <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'none' }}>
                          Click any card to inspect full prompt & context
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '12px' }}>
                        {(user.cases || []).map((c, cIdx) => {
                          const catStyle = getCategoryColor(c.chat_type);
                          return (
                            <div
                              key={cIdx}
                              onClick={() => setActiveModalCase({ ...c, user_name: displayName, user_email: user.email })}
                              style={{
                                background: 'rgba(30, 41, 59, 0.8)',
                                border: '1px solid rgba(255, 255, 255, 0.08)',
                                borderRadius: '10px',
                                padding: '14px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'space-between'
                              }}
                              onMouseEnter={(e) => e.currentTarget.style.borderColor = '#6366f1'}
                              onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'}
                            >
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
                                  <span style={{
                                    background: catStyle.bg,
                                    color: catStyle.text,
                                    border: `1px solid ${catStyle.border}`,
                                    borderRadius: '4px',
                                    padding: '2px 6px',
                                    fontSize: '10px',
                                    fontWeight: '700'
                                  }}>
                                    {catStyle.icon} {c.chat_type}
                                  </span>
                                  <span style={{ fontSize: '11px', color: '#64748b' }}>
                                    {c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Recent'}
                                  </span>
                                </div>

                                <div style={{ fontSize: '14px', fontWeight: '700', color: '#f8fafc', marginBottom: '4px' }}>
                                  {c.title}
                                </div>

                                {c.client_name && c.client_name !== 'N/A' && (
                                  <div style={{ fontSize: '11px', color: '#38bdf8', marginBottom: '6px', fontWeight: '600' }}>
                                    👤 Client: {c.client_name}
                                  </div>
                                )}

                                <p style={{
                                  fontSize: '12px',
                                  color: '#94a3b8',
                                  margin: 0,
                                  lineHeight: '1.4',
                                  display: '-webkit-box',
                                  WebkitLineClamp: 3,
                                  WebkitBoxOrient: 'vertical',
                                  overflow: 'hidden'
                                }}>
                                  {c.summary || 'Consultation session active.'}
                                </p>
                              </div>

                              <div style={{
                                marginTop: '12px',
                                paddingTop: '8px',
                                borderTop: '1px solid rgba(255, 255, 255, 0.04)',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                fontSize: '11px',
                                color: '#64748b'
                              }}>
                                <span>🧠 {c.model_name || 'gpt-4o'} ({c.tokens || 135} tokens)</span>
                                <span style={{ color: '#818cf8', fontWeight: '700' }}>Inspect 🔍</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Pagination Controls (Lightweight DOM) */}
            {totalUserPages > 1 && (
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '12px',
                padding: '12px 16px',
                background: 'rgba(15, 23, 42, 0.6)',
                borderRadius: '10px',
                border: '1px solid rgba(255, 255, 255, 0.06)'
              }}>
                <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                  Showing page <strong style={{ color: '#f8fafc' }}>{userPage}</strong> of <strong style={{ color: '#f8fafc' }}>{totalUserPages}</strong> ({filteredUsers.length} users total)
                </span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    disabled={userPage <= 1}
                    onClick={() => setUserPage(p => Math.max(p - 1, 1))}
                    style={{
                      background: userPage <= 1 ? 'rgba(255,255,255,0.04)' : 'rgba(99, 102, 241, 0.2)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: userPage <= 1 ? '#64748b' : '#a5b4fc',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: userPage <= 1 ? 'not-allowed' : 'pointer'
                    }}
                  >
                    ← Previous
                  </button>
                  <button
                    disabled={userPage >= totalUserPages}
                    onClick={() => setUserPage(p => Math.min(p + 1, totalUserPages))}
                    style={{
                      background: userPage >= totalUserPages ? 'rgba(255,255,255,0.04)' : 'rgba(99, 102, 241, 0.2)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: userPage >= totalUserPages ? '#64748b' : '#a5b4fc',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: '700',
                      cursor: userPage >= totalUserPages ? 'not-allowed' : 'pointer'
                    }}
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* FULL RECORD INSPECTION MODAL */}
      {activeModalCase && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 9999,
          padding: '20px'
        }}>
          <div style={{
            background: '#0f172a',
            border: '1px solid #6366f1',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '640px',
            maxHeight: '85vh',
            overflowY: 'auto',
            padding: '26px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{
                  ...getCategoryColor(activeModalCase.chat_type),
                  borderRadius: '6px',
                  padding: '3px 8px',
                  fontSize: '11px',
                  fontWeight: '700',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginBottom: '8px'
                }}>
                  {getCategoryColor(activeModalCase.chat_type).icon} {activeModalCase.chat_type}
                </span>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '18px', fontWeight: '800', color: '#f8fafc' }}>
                  {activeModalCase.title}
                </h3>
              </div>
              <button
                onClick={() => setActiveModalCase(null)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', background: 'rgba(30, 41, 59, 0.5)', padding: '14px', borderRadius: '10px' }}>
              <div>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '700' }}>USER / INITIATOR</div>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#f8fafc' }}>{activeModalCase.user_name}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>{activeModalCase.user_email}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '700' }}>CLIENT / CONTEXT</div>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#38bdf8' }}>{activeModalCase.client_name || 'General Inquiry'}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  {activeModalCase.created_at ? new Date(activeModalCase.created_at).toLocaleString() : 'N/A'}
                </div>
              </div>
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#818cf8', marginBottom: '6px', textTransform: 'uppercase' }}>
                📝 Case Summary & Prompt Details
              </div>
              <div style={{
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '14px',
                fontSize: '13px',
                lineHeight: '1.6',
                color: '#cbd5e1',
                whiteSpace: 'pre-wrap'
              }}>
                {activeModalCase.summary || 'No detailed summary recorded.'}
              </div>
            </div>

            {activeModalCase.key_issue && (
              <div>
                <div style={{ fontSize: '12px', fontWeight: '700', color: '#fbbf24', marginBottom: '6px', textTransform: 'uppercase' }}>
                  ⚖️ Key Legal Issue / Arguments
                </div>
                <div style={{
                  background: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  padding: '14px',
                  fontSize: '13px',
                  lineHeight: '1.6',
                  color: '#fde68a'
                }}>
                  {activeModalCase.key_issue}
                </div>
              </div>
            )}

            <button
              onClick={() => setActiveModalCase(null)}
              style={{
                background: '#6366f1',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '10px',
                fontWeight: '700',
                cursor: 'pointer',
                marginTop: '6px'
              }}
            >
              Close Record
            </button>
          </div>
        </div>
      )}

      {/* PROMPT ACTIVITY TIMELINE CHART */}
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
                <span>📈</span> {currentConfig.name} — Activity Timeline
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
                Timeseries activity tracking over recent active days
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
                        Avg Latency: {formatLatency(hoveredPoint.avg_latency)}
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
              <span>🧠</span> Foundation Model Split & Tokens ({currentConfig.name})
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
              Execution throughput and token consumption across deployed foundation models
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>Loading model analytics...</div>
        ) : !telemetry?.model_share || telemetry.model_share.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#64748b' }}>
            No chat events recorded yet for {currentConfig.name}.
          </div>
        ) : (
          <div className="table-responsive" style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', textAlign: 'left', color: '#94a3b8', fontSize: '12px' }}>
                  <th style={{ padding: '12px 14px' }}>AI Model</th>
                  <th style={{ padding: '12px 14px' }}>Request Count</th>
                  <th style={{ padding: '12px 14px' }}>Total Tokens Consumed</th>
                  <th style={{ padding: '12px 14px' }}>Usage Share</th>
                </tr>
              </thead>
              <tbody>
                {telemetry.model_share.map((m, idx) => {
                  const percentage = telemetry.total_tokens > 0 ? ((m.tokens / telemetry.total_tokens) * 100).toFixed(1) : '0.0';
                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', fontSize: '13px' }}>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{
                          background: 'rgba(99, 102, 241, 0.15)',
                          color: '#a5b4fc',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontWeight: '700',
                          fontSize: '12px',
                          fontFamily: 'monospace'
                        }}>
                          ⚡ {m.model}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: '700', color: '#f8fafc' }}>
                        {m.count.toLocaleString()} calls
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: '700', color: '#c084fc' }}>
                        {m.tokens.toLocaleString()} tokens
                      </td>
                      <td style={{ padding: '12px 14px' }}>
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
                <span>⚡</span> {currentConfig.name} — Recent Session Stream
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
                Live stream of latest prompt requests recorded from {currentConfig.platform}
              </p>
            </div>
          </div>

          <div className="table-responsive" style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', textAlign: 'left', color: '#94a3b8', fontSize: '12px' }}>
                  <th style={{ padding: '12px 14px' }}>User / Interaction</th>
                  <th style={{ padding: '12px 14px' }}>Topic / Category</th>
                  <th style={{ padding: '12px 14px' }}>Application</th>
                  <th style={{ padding: '12px 14px' }}>Model</th>
                  <th style={{ padding: '12px 14px' }}>Tokens</th>
                  <th style={{ padding: '12px 14px' }}>Latency</th>
                  <th style={{ padding: '12px 14px' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {paginatedSessions.map((s, idx) => {
                  const catStyle = getCategoryColor(s.chat_type);
                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', fontSize: '13px' }}>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ fontWeight: '700', color: '#f8fafc' }}>
                          {s.user_name || s.session_id}
                        </div>
                        {s.user_email && (
                          <div style={{ fontSize: '11px', color: '#64748b' }}>
                            {s.user_email}
                          </div>
                        )}
                        {s.preview && (
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '3px', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            "{s.preview}"
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{
                          background: catStyle.bg,
                          color: catStyle.text,
                          border: `1px solid ${catStyle.border}`,
                          padding: '2px 8px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: '700',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          {catStyle.icon} {s.chat_type}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: '700', color: '#f8fafc' }}>
                        {s.app_code}
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{
                          background: 'rgba(99, 102, 241, 0.15)',
                          color: '#a5b4fc',
                          padding: '2px 6px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontFamily: 'monospace',
                          fontWeight: '600'
                        }}>
                          {s.model_name}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', fontWeight: '700', color: '#c084fc' }}>
                        {s.total_tokens.toLocaleString()}
                      </td>
                      <td style={{ padding: '12px 14px', color: '#fbbf24', fontWeight: '600' }}>
                        {formatLatency(s.latency_ms)}
                      </td>
                      <td style={{ padding: '12px 14px', color: '#94a3b8', fontSize: '12px' }}>
                        {s.created_at ? new Date(s.created_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Session Stream Pagination Controls */}
          {totalSessionPages > 1 && (
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '12px',
              paddingTop: '12px',
              borderTop: '1px solid rgba(255, 255, 255, 0.06)'
            }}>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                Page <strong style={{ color: '#f8fafc' }}>{sessionPage}</strong> of <strong style={{ color: '#f8fafc' }}>{totalSessionPages}</strong>
              </span>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  disabled={sessionPage <= 1}
                  onClick={() => setSessionPage(p => Math.max(p - 1, 1))}
                  style={{
                    background: sessionPage <= 1 ? 'rgba(255,255,255,0.04)' : 'rgba(99, 102, 241, 0.2)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    color: sessionPage <= 1 ? '#64748b' : '#a5b4fc',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: sessionPage <= 1 ? 'not-allowed' : 'pointer'
                  }}
                >
                  ← Prev
                </button>
                <button
                  disabled={sessionPage >= totalSessionPages}
                  onClick={() => setSessionPage(p => Math.min(p + 1, totalSessionPages))}
                  style={{
                    background: sessionPage >= totalSessionPages ? 'rgba(255,255,255,0.04)' : 'rgba(99, 102, 241, 0.2)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    color: sessionPage >= totalSessionPages ? '#64748b' : '#a5b4fc',
                    padding: '4px 10px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: sessionPage >= totalSessionPages ? 'not-allowed' : 'pointer'
                  }}
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
