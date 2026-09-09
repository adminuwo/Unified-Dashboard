import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export const MarketingCampaignsTab = () => {
  const { token } = useAuth();

  // State
  const [links, setLinks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterProduct, setFilterProduct] = useState('all');
  const [filterPlatform, setFilterPlatform] = useState('all');

  // Generator Modal State
  const [showModal, setShowModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState('aisa');
  const [customTargetUrl, setCustomTargetUrl] = useState('');
  const [campaignName, setCampaignName] = useState('');
  const [postName, setPostName] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState(['instagram']);
  const [channelType, setChannelType] = useState('organic');
  const [customSlug, setCustomSlug] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedBatchResult, setGeneratedBatchResult] = useState(null);

  // QR Code & Details Modal State
  const [qrModalLink, setQrModalLink] = useState(null);
  const [detailsModalLink, setDetailsModalLink] = useState(null);
  const [copyFeedback, setCopyFeedback] = useState('');

  // Auto-Refresh & Live Telemetry State
  const [isLiveActive, setIsLiveActive] = useState(true);
  const [autoRefreshCountdown, setAutoRefreshCountdown] = useState(10);
  const [lastSynced, setLastSynced] = useState(null);

  // Test Install Simulation Modal State
  const [testInstallModalLink, setTestInstallModalLink] = useState(null);
  const [installPlatform, setInstallPlatform] = useState('android');
  const [installDeviceId, setInstallDeviceId] = useState('');
  const [installAppVersion, setInstallAppVersion] = useState('1.0.0');
  const [installClientIp, setInstallClientIp] = useState('127.0.0.1');
  const [installReferrerCustom, setInstallReferrerCustom] = useState('');
  const [isSubmittingInstall, setIsSubmittingInstall] = useState(false);
  const [installTestResult, setInstallTestResult] = useState(null);

  // Default fallback catalog if API is loading
  const defaultProducts = {
    aisa: { name: 'AISA', url: 'https://aisa24.com', color: '#6366F1', icon: '🤖' },
    aimall: { name: 'AI-Mall', url: 'https://aimall24.com', color: '#8B5CF6', icon: '🛍️' },
    efv: { name: 'EFV Franchise', url: 'https://efv.uwo24.com', color: '#10B981', icon: '⚡' },
    ailegal: { name: 'AI-Legal', url: 'https://ailegal.aisa24.com', color: '#D4AF37', icon: '⚖️' },
    uwo: { name: 'UWO Web', url: 'https://uwo24.com', color: '#3B82F6', icon: '🌐' },
    uwoconnect: { name: 'UWO Connect', url: 'https://connect.uwo24.com', color: '#EC4899', icon: '🔐' },
    yugamc: { name: 'Yugamc', url: 'https://yugamc.com', color: '#F59E0B', icon: '🏭' },
    custom: { name: 'Custom URL', url: '', color: '#94A3B8', icon: '🔗' },
  };

  const defaultPlatforms = {
    instagram: { name: 'Instagram', icon: '📸', color: '#E1306C' },
    linkedin: { name: 'LinkedIn', icon: '💼', color: '#0A66C2' },
    youtube: { name: 'YouTube', icon: '▶️', color: '#FF0000' },
    twitter: { name: 'Twitter / X', icon: '🐦', color: '#1DA1F2' },
    whatsapp: { name: 'WhatsApp', icon: '💬', color: '#25D366' },
    meta_ads: { name: 'Meta Ads', icon: '📢', color: '#1877F2' },
    google_ads: { name: 'Google Ads', icon: '🎯', color: '#4285F4' },
    reddit: { name: 'Reddit', icon: '🤖', color: '#FF4500' },
    telegram: { name: 'Telegram', icon: '✈️', color: '#0088CC' },
    email: { name: 'Newsletter', icon: '✉️', color: '#64748B' },
    influencer: { name: 'Influencer', icon: '⭐', color: '#A855F7' },
    other: { name: 'Custom Ref', icon: '🔗', color: '#475569' },
  };

  const products = config?.products || defaultProducts;
  const platforms = config?.platforms || defaultPlatforms;

  const fetchData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const headers = { Authorization: `Bearer ${token}` };

      const [cfgRes, sumRes, linksRes] = await Promise.all([
        fetch('/api/marketing/config', { headers }).catch(() => null),
        fetch('/api/marketing/analytics/summary', { headers }).catch(() => null),
        fetch('/api/marketing/links?limit=300', { headers }).catch(() => null),
      ]);

      if (cfgRes && cfgRes.ok) {
        const cfgData = await cfgRes.json();
        setConfig(cfgData);
      }

      if (sumRes && sumRes.ok) {
        const sumData = await sumRes.json();
        setSummary(sumData);
      }

      if (linksRes && linksRes.ok) {
        const linksData = await linksRes.json();
        setLinks(Array.isArray(linksData) ? linksData : []);
      }
      setLastSynced(new Date());
    } catch (err) {
      console.error('Error fetching marketing telemetry:', err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  // Real-time Auto-Refresh interval (every second decrements countdown, triggers silent update on 0)
  useEffect(() => {
    if (!isLiveActive) return;

    const timer = setInterval(() => {
      setAutoRefreshCountdown((prev) => {
        if (prev <= 1) {
          fetchData(true);
          return 10;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isLiveActive, token]);

  // Immediate refresh on window focus
  useEffect(() => {
    const handleFocus = () => {
      if (isLiveActive) {
        fetchData(true);
      }
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [isLiveActive, token]);

  const getShortUrl = (linkObj) => {
    if (!linkObj) return '';
    // If backend provided a custom short URL that doesn't point to localhost, use it
    if (linkObj.short_url && !linkObj.short_url.includes('localhost') && !linkObj.short_url.includes('127.0.0.1')) {
      return linkObj.short_url;
    }
    // In production or browser, dynamically use current window origin (e.g. https://unified.aisa24.com)
    return `${window.location.origin}/r/${linkObj.slug}`;
  };

  const handleCopy = (text, label) => {
    navigator.clipboard.writeText(text);
    setCopyFeedback(`${label} copied!`);
    setTimeout(() => setCopyFeedback(''), 2500);
  };

  const togglePlatform = (pKey) => {
    setSelectedPlatforms((prev) =>
      prev.includes(pKey)
        ? prev.length > 1
          ? prev.filter((k) => k !== pKey)
          : prev
        : [...prev, pKey]
    );
  };

  const selectAllPlatforms = () => {
    setSelectedPlatforms(Object.keys(platforms).filter((k) => k !== 'other'));
  };

  const clearPlatforms = () => {
    setSelectedPlatforms(['instagram']);
  };

  const handleCreateLinks = async (e) => {
    e.preventDefault();
    if (!campaignName.trim() || !postName.trim() || selectedPlatforms.length === 0) return;

    try {
      setIsSubmitting(true);
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      };

      let result;
      if (selectedPlatforms.length === 1) {
        const res = await fetch('/api/marketing/links', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            product_id: selectedProduct,
            custom_target_url: customTargetUrl || undefined,
            platform: selectedPlatforms[0],
            campaign_name: campaignName.trim(),
            post_name: postName.trim(),
            channel_type: channelType,
            custom_slug: customSlug.trim() || undefined,
            notes: notes.trim() || undefined,
          }),
        });
        const data = await res.json();
        result = [data];
      } else {
        const res = await fetch('/api/marketing/links/batch', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            product_id: selectedProduct,
            custom_target_url: customTargetUrl || undefined,
            campaign_name: campaignName.trim(),
            post_name: postName.trim(),
            platforms: selectedPlatforms,
            channel_type: channelType,
            notes: notes.trim() || undefined,
          }),
        });
        result = await res.json();
      }

      setGeneratedBatchResult(Array.isArray(result) ? result : [result]);
      fetchData();
    } catch (err) {
      console.error('Failed to create marketing links:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (linkId, currentStatus) => {
    try {
      const res = await fetch(`/api/marketing/links/${linkId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ is_active: !currentStatus }),
      });
      if (res.ok) {
        setLinks((prev) =>
          prev.map((l) => (l.id === linkId ? { ...l, is_active: !currentStatus } : l))
        );
      }
    } catch (err) {
      console.error('Failed to toggle status:', err);
    }
  };

  const handleDelete = async (linkId) => {
    if (!window.confirm('Are you sure you want to delete this marketing link and its click logs?')) return;
    try {
      const res = await fetch(`/api/marketing/links/${linkId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setLinks((prev) => prev.filter((l) => l.id !== linkId));
        fetchData();
      }
    } catch (err) {
      console.error('Failed to delete link:', err);
    }
  };

  const openDetails = async (link) => {
    try {
      const res = await fetch(`/api/marketing/links/${link.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDetailsModalLink(data);
      }
    } catch (err) {
      console.error('Failed to fetch details:', err);
    }
  };

  const openTestInstallModal = (link) => {
    const randomHex = Math.random().toString(36).substring(2, 10);
    setTestInstallModalLink(link);
    setInstallPlatform('android');
    setInstallDeviceId(`dev_test_${randomHex}`);
    setInstallAppVersion('1.0.0');
    setInstallClientIp('127.0.0.1');
    setInstallReferrerCustom(`utm_source=referral&slug=${link.slug}&utm_content=mobile`);
    setInstallTestResult(null);
  };

  const handleSimulateInstall = async (e) => {
    e.preventDefault();
    if (!testInstallModalLink) return;
    setIsSubmittingInstall(true);
    setInstallTestResult(null);
    try {
      const payload = {
        platform: installPlatform,
        app_code: testInstallModalLink.product_id,
        slug: testInstallModalLink.slug,
        referral_code: testInstallModalLink.slug,
        device_id: installDeviceId || `dev_${Math.random().toString(36).substring(2, 10)}`,
        version: installAppVersion || '1.0.0',
        ip: installClientIp || '127.0.0.1',
      };

      if (installPlatform === 'android') {
        payload.install_referrer = installReferrerCustom || `utm_source=referral&slug=${testInstallModalLink.slug}`;
      }

      const res = await fetch('/api/marketing/telemetry/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      setInstallTestResult({
        ok: res.ok,
        status: res.status,
        data,
      });

      if (res.ok) {
        // Trigger real-time update
        fetchData(true);
        if (detailsModalLink && (detailsModalLink.link?.id === testInstallModalLink.id || detailsModalLink.link?.slug === testInstallModalLink.slug)) {
          openDetails(testInstallModalLink);
        }
      }
    } catch (err) {
      setInstallTestResult({
        ok: false,
        error: err.message,
      });
    } finally {
      setIsSubmittingInstall(false);
    }
  };

  // Filtered links
  const filteredLinks = links.filter((l) => {
    const matchSearch =
      !searchTerm.trim() ||
      (l.post_name && l.post_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (l.campaign_name && l.campaign_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (l.slug && l.slug.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (l.product_name && l.product_name.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchProduct = filterProduct === 'all' || l.product_id === filterProduct;
    const matchPlatform = filterPlatform === 'all' || l.platform === filterPlatform;

    return matchSearch && matchProduct && matchPlatform;
  });

  return (
    <div className="marketing-tab-container" style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box', color: '#F8FAFC' }}>
      {/* Toast Feedback */}
      {copyFeedback && (
        <div
          style={{
            position: 'fixed',
            bottom: '30px',
            right: '30px',
            zIndex: 9999,
            backgroundColor: '#10B981',
            color: '#FFFFFF',
            padding: '12px 24px',
            borderRadius: '12px',
            fontWeight: 'bold',
            boxShadow: '0 10px 30px rgba(16,185,129,0.4)',
            animation: 'fadeIn 0.2s ease',
          }}
        >
          ✓ {copyFeedback}
        </div>
      )}

      {/* Top Header & Action Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '900', margin: 0, letterSpacing: '-0.5px' }}>
            📢 Marketing Campaigns & Referral Tracking
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '13px', margin: '4px 0 0 0' }}>
            Generate multi-platform UTM URLs, short links & track exact reach per post across all 7 products
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={fetchData}
            style={{
              padding: '10px 18px',
              borderRadius: '12px',
              backgroundColor: '#1E293B',
              border: '1px solid #334155',
              color: '#F8FAFC',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            🔄 Refresh
          </button>

          <button
            onClick={() => {
              setGeneratedBatchResult(null);
              setShowModal(true);
            }}
            style={{
              padding: '10px 22px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
              border: 'none',
              color: '#FFFFFF',
              fontWeight: '800',
              fontSize: '13px',
              cursor: 'pointer',
              boxShadow: '0 8px 25px rgba(99,102,241,0.35)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            🚀 + Generate Tracked Link
          </button>
        </div>
      </div>

      {/* Live Real-time Auto-Sync Status Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: isLiveActive ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
          border: `1px solid ${isLiveActive ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
          borderRadius: '14px',
          padding: '10px 18px',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '12px',
          boxShadow: '0 4px 15px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              width: '9px',
              height: '9px',
              borderRadius: '50%',
              background: isLiveActive ? '#10B981' : '#F59E0B',
              boxShadow: isLiveActive ? '0 0 10px #10B981' : '0 0 10px #F59E0B',
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: '13px', color: isLiveActive ? '#34D399' : '#FBBF24', fontWeight: '800' }}>
            {isLiveActive ? '⚡ Real-time Referral & Install Telemetry Active' : '⏸️ Auto-Sync Paused'}
          </span>
          {lastSynced && (
            <span style={{ fontSize: '12px', color: '#94A3B8' }}>
              • Last synced: {lastSynced.toLocaleTimeString()}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {isLiveActive && (
            <span style={{ fontSize: '12px', color: '#94A3B8' }}>
              Auto-refresh in <strong style={{ color: '#38BDF8', fontWeight: '800' }}>{autoRefreshCountdown}s</strong>
            </span>
          )}
          <button
            onClick={() => setIsLiveActive((prev) => !prev)}
            style={{
              background: 'transparent',
              border: '1px solid #334155',
              color: '#94A3B8',
              borderRadius: '8px',
              padding: '5px 12px',
              fontSize: '11px',
              fontWeight: '700',
              cursor: 'pointer',
            }}
          >
            {isLiveActive ? '⏸️ Pause' : '▶️ Resume'}
          </button>
          <button
            onClick={() => fetchData(false)}
            disabled={loading}
            style={{
              background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%)',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              color: '#38BDF8',
              borderRadius: '8px',
              padding: '5px 14px',
              fontSize: '11px',
              fontWeight: '800',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '⟳ Syncing...' : '⟳ Refresh Now'}
          </button>
        </div>
      </div>

      {/* KPI Cards Grid - Balanced 3 + 2 Architecture */}
      <div style={{ marginBottom: '28px', width: '100%' }}>
        {/* Row 1: Core Growth Metrics (3 Cards) */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            marginBottom: '16px',
          }}
        >
          {/* Total Clicks */}
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #1E293B',
              borderRadius: '16px',
              padding: '18px 20px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
              <span style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                Total Referral Clicks
              </span>
              <span style={{ fontSize: '18px' }}>🖱️</span>
            </div>
            <div style={{ fontSize: '30px', fontWeight: '900', color: '#38BDF8', marginTop: '8px' }}>
              {summary?.total_clicks?.toLocaleString() || '0'}
            </div>
            <div style={{ fontSize: '12px', color: '#64748B', marginTop: '4px' }}>
              Across {summary?.total_links || links.length} active campaigns
            </div>
          </div>

          {/* Unique Reach */}
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #1E293B',
              borderRadius: '16px',
              padding: '18px 20px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
              <span style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                Unique Audience Reach
              </span>
              <span style={{ fontSize: '18px' }}>👥</span>
            </div>
            <div style={{ fontSize: '30px', fontWeight: '900', color: '#10B981', marginTop: '8px' }}>
              {summary?.unique_reach?.toLocaleString() || '0'}
            </div>
            <div style={{ fontSize: '12px', color: '#64748B', marginTop: '4px' }}>
              Unique individuals visiting via links
            </div>
          </div>

          {/* App Downloads */}
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #1E293B',
              borderRadius: '16px',
              padding: '18px 20px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
              <span style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                App Downloads
              </span>
              <span style={{ fontSize: '18px' }}>📲</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', marginTop: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '30px', fontWeight: '900', color: '#A855F7' }}>
                {summary?.total_downloads?.toLocaleString() || '0'}
              </span>
              <div style={{ display: 'flex', gap: '6px', fontSize: '11px', fontWeight: '700' }}>
                <span
                  style={{
                    padding: '3px 8px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    color: '#34D399',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  🤖 Android: {summary?.android_downloads ?? summary?.downloads_by_platform?.android ?? 0}
                </span>
                <span
                  style={{
                    padding: '3px 8px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(56, 189, 248, 0.15)',
                    color: '#38BDF8',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  🍏 iOS: {summary?.ios_downloads ?? summary?.downloads_by_platform?.ios ?? 0}
                </span>
              </div>
            </div>
            <div style={{ fontSize: '12px', color: '#64748B', marginTop: '6px' }}>
              {summary?.overall_conversion_rate || 0}% overall conversion rate
            </div>
          </div>
        </div>

        {/* Row 2: Performance Leaders (2 Equal Width Cards) */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '16px',
          }}
        >
          {/* Best Performing Post */}
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #1E293B',
              borderRadius: '16px',
              padding: '18px 20px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
              <span style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                Best Performing Post
              </span>
              <span style={{ fontSize: '18px' }}>🏆</span>
            </div>
            <div
              style={{
                fontSize: '20px',
                fontWeight: '900',
                color: '#F59E0B',
                marginTop: '8px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
              title={summary?.top_post?.post_name || 'No post data yet'}
            >
              {summary?.top_post?.post_name || 'No post data yet'}
            </div>
            <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
              {summary?.top_post ? `${summary.top_post.total_clicks} clicks (${summary.top_post.platform})` : 'Start a campaign to view'}
            </div>
          </div>

          {/* Top Channel */}
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #1E293B',
              borderRadius: '16px',
              padding: '18px 20px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
              <span style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                Top Channel
              </span>
              <span style={{ fontSize: '18px' }}>📱</span>
            </div>
            <div
              style={{
                fontSize: '20px',
                fontWeight: '900',
                color: '#EC4899',
                marginTop: '8px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {summary?.top_platform ? `${summary.top_platform.name}` : 'No traffic yet'}
            </div>
            <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
              {summary?.top_platform ? `${summary.top_platform.clicks} clicks (${summary.top_platform.share_pct}%)` : 'Ready for tracking'}
            </div>
          </div>
        </div>
      </div>

      {/* Platform & Product Share Breakdown Graphs */}
      {summary && (summary.platform_distribution?.length > 0 || summary.product_distribution?.length > 0) && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
            gap: '18px',
            marginBottom: '28px',
          }}
        >
          {/* Platform Share Progress */}
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #1E293B',
              borderRadius: '18px',
              padding: '20px',
            }}
          >
            <h3 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 16px 0', color: '#F1F5F9' }}>
              📊 Social Platform Traffic Share
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {summary.platform_distribution.map((pd) => (
                <div key={pd.platform}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: '700' }}>
                      {pd.icon} {pd.name}
                    </span>
                    <span style={{ color: '#94A3B8' }}>
                      {pd.clicks} clicks ({pd.share_pct}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: '#1E293B', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${pd.share_pct}%`,
                        backgroundColor: pd.color || '#6366F1',
                        borderRadius: '4px',
                        transition: 'width 0.5s ease',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Product Click Distribution */}
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #1E293B',
              borderRadius: '18px',
              padding: '20px',
            }}
          >
            <h3 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 16px 0', color: '#F1F5F9' }}>
              🎯 Product Destination Traffic
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {summary.product_distribution.map((prd) => (
                <div key={prd.product_id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: '700' }}>
                      {products[prd.product_id]?.icon || '🚀'} {prd.name}
                    </span>
                    <span style={{ color: '#94A3B8' }}>
                      {prd.clicks} clicks ({prd.share_pct}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: '#1E293B', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${prd.share_pct}%`,
                        backgroundColor: prd.color || '#3B82F6',
                        borderRadius: '4px',
                        transition: 'width 0.5s ease',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div
        style={{
          backgroundColor: '#0F172A',
          border: '1px solid #1E293B',
          borderRadius: '16px',
          padding: '16px',
          marginBottom: '20px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '14px',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', gap: '12px', flex: 1, minWidth: '280px' }}>
          <input
            type="text"
            placeholder="🔍 Search post name, campaign or slug..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              flex: 1,
              padding: '10px 16px',
              backgroundColor: '#1E293B',
              border: '1px solid #334155',
              borderRadius: '10px',
              color: '#FFFFFF',
              fontSize: '13px',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {/* Product Filter */}
          <select
            value={filterProduct}
            onChange={(e) => setFilterProduct(e.target.value)}
            style={{
              padding: '10px 14px',
              backgroundColor: '#1E293B',
              border: '1px solid #334155',
              borderRadius: '10px',
              color: '#FFFFFF',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="all">All Products</option>
            {Object.entries(products).map(([k, v]) => (
              <option key={k} value={k}>
                {v.name}
              </option>
            ))}
          </select>

          {/* Platform Filter */}
          <select
            value={filterPlatform}
            onChange={(e) => setFilterPlatform(e.target.value)}
            style={{
              padding: '10px 14px',
              backgroundColor: '#1E293B',
              border: '1px solid #334155',
              borderRadius: '10px',
              color: '#FFFFFF',
              fontSize: '13px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="all">All Platforms</option>
            {Object.entries(platforms).map(([k, v]) => (
              <option key={k} value={k}>
                {v.icon} {v.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Links & Posts Comparison Table */}
      <div
        style={{
          backgroundColor: '#0F172A',
          border: '1px solid #1E293B',
          borderRadius: '18px',
          overflow: 'hidden',
          boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
        }}
      >
        <div style={{ width: '100%', maxWidth: '100%', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#1E293B', color: '#94A3B8', borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Post / Campaign Name</th>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Product</th>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Platform</th>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Short Redirect URL</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Total Clicks</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Unique Reach</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Downloads (🤖 / 🍏)</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Conv. %</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Status</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="10" style={{ padding: '40px', textAlign: 'center', color: '#94A3B8' }}>
                    Loading marketing links...
                  </td>
                </tr>
              ) : filteredLinks.length === 0 ? (
                <tr>
                  <td colSpan="10" style={{ padding: '40px', textAlign: 'center', color: '#94A3B8' }}>
                    No marketing links found. Click <strong>+ Generate Tracked Link</strong> above to create your first post campaign!
                  </td>
                </tr>
              ) : (
                filteredLinks.map((link) => {
                  const pInfo = platforms[link.platform] || { name: link.platform, icon: '🔗', color: '#64748B' };
                  const prodInfo = products[link.product_id] || { name: link.product_name, color: '#6366F1' };

                  return (
                    <tr
                      key={link.id}
                      style={{
                        borderBottom: '1px solid #1E293B',
                        transition: 'background-color 0.2s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#1E293B40')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      {/* Post Name & Campaign */}
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ fontWeight: '800', color: '#FFFFFF', fontSize: '14px' }}>{link.post_name}</div>
                        <div style={{ color: '#94A3B8', fontSize: '11px', marginTop: '2px' }}>
                          Campaign: <span style={{ color: '#CBD5E1' }}>{link.campaign_name}</span>
                        </div>
                      </td>

                      {/* Product Badge */}
                      <td style={{ padding: '14px 18px' }}>
                        <span
                          style={{
                            padding: '4px 10px',
                            borderRadius: '8px',
                            backgroundColor: `${prodInfo.color}20`,
                            color: prodInfo.color,
                            fontWeight: '700',
                            fontSize: '12px',
                            border: `1px solid ${prodInfo.color}40`,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          {prodInfo.icon || '🚀'} {link.product_name || prodInfo.name}
                        </span>
                      </td>

                      {/* Platform */}
                      <td style={{ padding: '14px 18px' }}>
                        <span
                          style={{
                            padding: '4px 10px',
                            borderRadius: '8px',
                            backgroundColor: `${pInfo.color}20`,
                            color: pInfo.color,
                            fontWeight: '700',
                            fontSize: '12px',
                            border: `1px solid ${pInfo.color}40`,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          {pInfo.icon} {pInfo.name}
                        </span>
                      </td>

                      {/* Short Link */}
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <code
                            style={{
                              backgroundColor: '#1E293B',
                              padding: '4px 8px',
                              borderRadius: '6px',
                              color: '#38BDF8',
                              fontSize: '12px',
                            }}
                          >
                            /r/{link.slug}
                          </code>
                          <button
                            onClick={() => handleCopy(getShortUrl(link), 'Short link')}
                            title="Copy Short URL"
                            style={{
                              backgroundColor: 'transparent',
                              border: 'none',
                              color: '#94A3B8',
                              cursor: 'pointer',
                              fontSize: '14px',
                            }}
                          >
                            📋
                          </button>
                        </div>
                      </td>

                      {/* Total Clicks */}
                      <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                        <span
                          style={{
                            fontWeight: '900',
                            fontSize: '15px',
                            color: link.total_clicks > 0 ? '#38BDF8' : '#64748B',
                          }}
                        >
                          {link.total_clicks}
                        </span>
                      </td>

                      {/* Unique Reach */}
                      <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                        <span
                          style={{
                            fontWeight: '800',
                            fontSize: '14px',
                            color: link.unique_clicks > 0 ? '#10B981' : '#64748B',
                          }}
                        >
                          {link.unique_clicks}
                        </span>
                      </td>

                      {/* Downloads */}
                      <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                          <span
                            style={{
                              fontWeight: '900',
                              fontSize: '15px',
                              color: (link.total_downloads || 0) > 0 ? '#A855F7' : '#64748B',
                            }}
                          >
                            {link.total_downloads || 0}
                          </span>
                          <div style={{ display: 'flex', gap: '4px', fontSize: '10px', fontWeight: '800' }}>
                            <span
                              title={`Android Downloads: ${link.android_downloads || 0}`}
                              style={{
                                padding: '2px 6px',
                                borderRadius: '6px',
                                backgroundColor: (link.android_downloads || 0) > 0 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(30, 41, 59, 0.8)',
                                color: (link.android_downloads || 0) > 0 ? '#34D399' : '#64748B',
                                border: '1px solid rgba(16, 185, 129, 0.25)',
                              }}
                            >
                              🤖 {link.android_downloads || 0}
                            </span>
                            <span
                              title={`iOS Downloads: ${link.ios_downloads || 0}`}
                              style={{
                                padding: '2px 6px',
                                borderRadius: '6px',
                                backgroundColor: (link.ios_downloads || 0) > 0 ? 'rgba(56, 189, 248, 0.2)' : 'rgba(30, 41, 59, 0.8)',
                                color: (link.ios_downloads || 0) > 0 ? '#38BDF8' : '#64748B',
                                border: '1px solid rgba(56, 189, 248, 0.25)',
                              }}
                            >
                              🍏 {link.ios_downloads || 0}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Conversion Rate */}
                      <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                        <span
                          style={{
                            fontWeight: '800',
                            fontSize: '12px',
                            padding: '3px 8px',
                            borderRadius: '6px',
                            backgroundColor: (link.total_downloads || 0) > 0 ? 'rgba(168, 85, 247, 0.18)' : 'rgba(100, 116, 139, 0.1)',
                            color: (link.total_downloads || 0) > 0 ? '#C084FC' : '#64748B',
                          }}
                        >
                          {link.total_clicks > 0
                            ? `${(((link.total_downloads || 0) / link.total_clicks) * 100).toFixed(1)}%`
                            : '0.0%'}
                        </span>
                      </td>

                      {/* Status */}
                      <td style={{ padding: '14px 18px', textAlign: 'center' }}>
                        <button
                          onClick={() => handleToggleStatus(link.id, link.is_active)}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '8px',
                            backgroundColor: link.is_active ? '#10B98120' : '#EF444420',
                            color: link.is_active ? '#10B981' : '#EF4444',
                            border: `1px solid ${link.is_active ? '#10B98140' : '#EF444440'}`,
                            fontSize: '11px',
                            fontWeight: '800',
                            cursor: 'pointer',
                          }}
                        >
                          {link.is_active ? '● Active' : '○ Paused'}
                        </button>
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          <button
                            onClick={() => handleCopy(link.full_destination_url, 'Full UTM URL')}
                            title="Copy Full UTM Destination URL"
                            style={{
                              padding: '6px 10px',
                              borderRadius: '8px',
                              backgroundColor: '#1E293B',
                              border: '1px solid #334155',
                              color: '#F8FAFC',
                              fontSize: '11px',
                              cursor: 'pointer',
                              fontWeight: '700',
                            }}
                          >
                            UTM 📋
                          </button>

                          <button
                            onClick={() => setQrModalLink(link)}
                            title="View / Download QR Code"
                            style={{
                              padding: '6px 10px',
                              borderRadius: '8px',
                              backgroundColor: '#1E293B',
                              border: '1px solid #334155',
                              color: '#F8FAFC',
                              fontSize: '11px',
                              cursor: 'pointer',
                              fontWeight: '700',
                            }}
                          >
                            QR 🏁
                          </button>

                          <button
                            onClick={() => openTestInstallModal(link)}
                            title="Simulate Real-time App Install Telemetry (Android / iOS)"
                            style={{
                              padding: '6px 10px',
                              borderRadius: '8px',
                              background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%)',
                              border: '1px solid rgba(168, 85, 247, 0.5)',
                              color: '#D8B4FE',
                              fontSize: '11px',
                              cursor: 'pointer',
                              fontWeight: '800',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            ⚡ Test Install
                          </button>

                          <button
                            onClick={() => openDetails(link)}
                            title="View Click & Install Telemetry"
                            style={{
                              padding: '6px 10px',
                              borderRadius: '8px',
                              backgroundColor: '#6366F120',
                              border: '1px solid #6366F140',
                              color: '#818CF8',
                              fontSize: '11px',
                              cursor: 'pointer',
                              fontWeight: '700',
                            }}
                          >
                            Stats 📈
                          </button>

                          <button
                            onClick={() => handleDelete(link.id)}
                            title="Delete Link"
                            style={{
                              padding: '6px 8px',
                              borderRadius: '8px',
                              backgroundColor: '#EF444415',
                              border: '1px solid #EF444430',
                              color: '#EF4444',
                              fontSize: '11px',
                              cursor: 'pointer',
                            }}
                          >
                            🗑️
                          </button>
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

      {/* ========================================================================= */}
      {/* 🚀 MODAL: Multi-Platform Campaign Link Generator Wizard */}
      {/* ========================================================================= */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 999,
            backgroundColor: 'rgba(0,0,0,0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '24px',
              padding: '28px',
              width: '100%',
              maxWidth: '680px',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: '0 25px 80px rgba(0,0,0,0.8)',
              color: '#F8FAFC',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: '900', margin: 0 }}>
                🚀 Generate Marketing & Referral Link
              </h3>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  backgroundColor: '#1E293B',
                  border: 'none',
                  color: '#94A3B8',
                  borderRadius: '10px',
                  width: '32px',
                  height: '32px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                }}
              >
                ✕
              </button>
            </div>

            {/* If Batch Result generated, show result cards */}
            {generatedBatchResult ? (
              <div>
                <div
                  style={{
                    backgroundColor: '#10B98115',
                    border: '1px solid #10B98140',
                    borderRadius: '14px',
                    padding: '16px',
                    marginBottom: '20px',
                    color: '#34D399',
                    fontSize: '14px',
                    fontWeight: '700',
                  }}
                >
                  🎉 Successfully created {generatedBatchResult.length} tracked link(s)!
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
                  {generatedBatchResult.map((resLink) => {
                    const p = platforms[resLink.platform] || { name: resLink.platform, icon: '🔗' };
                    const shortUrl = getShortUrl(resLink);
                    return (
                      <div
                        key={resLink.id || resLink.slug}
                        style={{
                          backgroundColor: '#1E293B',
                          borderRadius: '14px',
                          padding: '14px',
                          border: '1px solid #334155',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <span style={{ fontWeight: '800', fontSize: '13px' }}>
                            {p.icon} {p.name} — {resLink.post_name}
                          </span>
                          <span style={{ color: '#94A3B8', fontSize: '11px' }}>/r/{resLink.slug}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <input
                            type="text"
                            readOnly
                            value={shortUrl}
                            style={{
                              flex: 1,
                              backgroundColor: '#0F172A',
                              border: '1px solid #334155',
                              padding: '8px 12px',
                              borderRadius: '8px',
                              color: '#38BDF8',
                              fontSize: '12px',
                            }}
                          />
                          <button
                            onClick={() => handleCopy(shortUrl, `${p.name} Short link`)}
                            style={{
                              padding: '8px 14px',
                              backgroundColor: '#6366F1',
                              color: '#FFFFFF',
                              border: 'none',
                              borderRadius: '8px',
                              fontWeight: '700',
                              fontSize: '12px',
                              cursor: 'pointer',
                            }}
                          >
                            Copy 📋
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <button
                  onClick={() => setShowModal(false)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '12px',
                    backgroundColor: '#1E293B',
                    border: '1px solid #334155',
                    color: '#F8FAFC',
                    fontWeight: '800',
                    cursor: 'pointer',
                  }}
                >
                  Done & Close
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreateLinks}>
                {/* 1. Select Product */}
                <div style={{ marginBottom: '18px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '8px' }}>
                    1. Select Target Ecosystem Product
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                    {Object.entries(products).map(([k, v]) => (
                      <button
                        type="button"
                        key={k}
                        onClick={() => setSelectedProduct(k)}
                        style={{
                          padding: '10px 8px',
                          borderRadius: '12px',
                          backgroundColor: selectedProduct === k ? `${v.color}25` : '#1E293B',
                          border: `2px solid ${selectedProduct === k ? v.color : '#334155'}`,
                          color: '#FFFFFF',
                          fontWeight: selectedProduct === k ? '800' : '600',
                          fontSize: '12px',
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        <span style={{ fontSize: '18px' }}>{v.icon || '🚀'}</span>
                        <span>{v.name}</span>
                      </button>
                    ))}
                  </div>

                  {/* Quick Google Play Store Link Presets */}
                  <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: '800', textTransform: 'uppercase' }}>
                      App Store Presets:
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedProduct('ailegal');
                        setCustomTargetUrl('https://play.google.com/store/apps/details?id=com.uwo.ailegal');
                      }}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '8px',
                        backgroundColor: customTargetUrl.includes('com.uwo.ailegal') ? 'rgba(16,185,129,0.2)' : '#1E293B',
                        border: `1px solid ${customTargetUrl.includes('com.uwo.ailegal') ? '#10B981' : '#334155'}`,
                        color: customTargetUrl.includes('com.uwo.ailegal') ? '#34D399' : '#CBD5E1',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      🤖 AI Legal Play Store
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedProduct('aisa');
                        setCustomTargetUrl('https://play.google.com/store/apps/details?id=com.uwo.aisa');
                      }}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '8px',
                        backgroundColor: customTargetUrl.includes('com.uwo.aisa') ? 'rgba(16,185,129,0.2)' : '#1E293B',
                        border: `1px solid ${customTargetUrl.includes('com.uwo.aisa') ? '#10B981' : '#334155'}`,
                        color: customTargetUrl.includes('com.uwo.aisa') ? '#34D399' : '#CBD5E1',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      🤖 AISA Play Store
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedProduct('ailegal');
                        setCustomTargetUrl('https://apps.apple.com/app/id6797449251');
                      }}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '8px',
                        backgroundColor: customTargetUrl.includes('id6797449251') ? 'rgba(59,130,246,0.2)' : '#1E293B',
                        border: `1px solid ${customTargetUrl.includes('id6797449251') ? '#3B82F6' : '#334155'}`,
                        color: customTargetUrl.includes('id6797449251') ? '#60A5FA' : '#CBD5E1',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      🍏 AI Legal App Store
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedProduct('aisa');
                        setCustomTargetUrl('https://apps.apple.com/app/id6779135418');
                      }}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '8px',
                        backgroundColor: customTargetUrl.includes('id6779135418') ? 'rgba(59,130,246,0.2)' : '#1E293B',
                        border: `1px solid ${customTargetUrl.includes('id6779135418') ? '#3B82F6' : '#334155'}`,
                        color: customTargetUrl.includes('id6779135418') ? '#60A5FA' : '#CBD5E1',
                        fontSize: '12px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      🍏 AISA App Store
                    </button>
                    {customTargetUrl ? (
                      <button
                        type="button"
                        onClick={() => setCustomTargetUrl('')}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '8px',
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: '#EF4444',
                          fontSize: '11px',
                          fontWeight: '700',
                          cursor: 'pointer',
                        }}
                      >
                        ✕ Reset to Web Default
                      </button>
                    ) : null}
                  </div>

                  {customTargetUrl.includes('play.google.com') && (
                    <div
                      style={{
                        marginTop: '10px',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        backgroundColor: 'rgba(16,185,129,0.12)',
                        border: '1px solid rgba(16,185,129,0.3)',
                        color: '#34D399',
                        fontSize: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <span>✨</span>
                      <span>
                        <strong>Google Play Install Referrer Active!</strong> Installs from this link will be automatically tracked in the <strong>Downloads</strong> column.
                      </span>
                    </div>
                  )}
                </div>

                {/* Custom URL Input if selected */}
                {selectedProduct === 'custom' && (
                  <div style={{ marginBottom: '18px' }}>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                      Custom Landing URL
                    </label>
                    <input
                      type="url"
                      required
                      placeholder="https://yourdomain.com/special-page"
                      value={customTargetUrl}
                      onChange={(e) => setCustomTargetUrl(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        backgroundColor: '#1E293B',
                        border: '1px solid #334155',
                        borderRadius: '10px',
                        color: '#FFFFFF',
                        fontSize: '13px',
                      }}
                    />
                  </div>
                )}

                {/* 2. Campaign Name & Post Identifier */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '18px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                      2. Campaign Group Name
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. diwali_sale, launch_v2"
                      value={campaignName}
                      onChange={(e) => setCampaignName(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        backgroundColor: '#1E293B',
                        border: '1px solid #334155',
                        borderRadius: '10px',
                        color: '#FFFFFF',
                        fontSize: '13px',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                      3. Post Identifier / Title
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Reel 1 - AI Lawyer, Story 5"
                      value={postName}
                      onChange={(e) => setPostName(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        backgroundColor: '#1E293B',
                        border: '1px solid #334155',
                        borderRadius: '10px',
                        color: '#FFFFFF',
                        fontSize: '13px',
                      }}
                    />
                  </div>
                </div>

                {/* 3. Multi-Platform Selection */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <label style={{ fontSize: '12px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase' }}>
                      4. Select Social Platforms ({selectedPlatforms.length} selected)
                    </label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        onClick={selectAllPlatforms}
                        style={{ background: 'none', border: 'none', color: '#818CF8', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        onClick={clearPlatforms}
                        style={{ background: 'none', border: 'none', color: '#94A3B8', fontSize: '11px', cursor: 'pointer' }}
                      >
                        Reset
                      </button>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                    {Object.entries(platforms).map(([k, v]) => {
                      const isSelected = selectedPlatforms.includes(k);
                      return (
                        <div
                          key={k}
                          onClick={() => togglePlatform(k)}
                          style={{
                            padding: '8px 12px',
                            borderRadius: '10px',
                            backgroundColor: isSelected ? `${v.color}25` : '#1E293B',
                            border: `1.5px solid ${isSelected ? v.color : '#334155'}`,
                            color: isSelected ? '#FFFFFF' : '#94A3B8',
                            fontSize: '12px',
                            fontWeight: isSelected ? '800' : '600',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            userSelect: 'none',
                          }}
                        >
                          <span>{v.icon}</span>
                          <span>{v.name}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Optional Custom Slug */}
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                    Custom Short Slug (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. try-aisa-free (leave blank for automatic smart slug)"
                    value={customSlug}
                    onChange={(e) => setCustomSlug(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      backgroundColor: '#1E293B',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#FFFFFF',
                      fontSize: '13px',
                    }}
                  />
                </div>

                {/* Submit CTA */}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    width: '100%',
                    padding: '14px',
                    borderRadius: '14px',
                    background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
                    border: 'none',
                    color: '#FFFFFF',
                    fontWeight: '900',
                    fontSize: '14px',
                    cursor: 'pointer',
                    boxShadow: '0 10px 30px rgba(99,102,241,0.4)',
                  }}
                >
                  {isSubmitting ? 'Generating Tracked Links...' : `🚀 Generate ${selectedPlatforms.length} Tracked Link(s)`}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 🏁 QR CODE MODAL */}
      {/* ========================================================================= */}
      {qrModalLink && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 999,
            backgroundColor: 'rgba(0,0,0,0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '24px',
              padding: '28px',
              width: '100%',
              maxWidth: '400px',
              textAlign: 'center',
              color: '#F8FAFC',
            }}
          >
            <h3 style={{ fontSize: '18px', fontWeight: '900', margin: '0 0 6px 0' }}>🏁 Campaign QR Code</h3>
            <p style={{ color: '#94A3B8', fontSize: '12px', margin: '0 0 20px 0' }}>
              {qrModalLink.post_name} ({qrModalLink.platform})
            </p>

            {/* QR Image generated via quick Google Chart API or data URL */}
            <div style={{ backgroundColor: '#FFFFFF', padding: '16px', borderRadius: '16px', display: 'inline-block', marginBottom: '20px' }}>
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(
                  getShortUrl(qrModalLink)
                )}`}
                alt="QR Code"
                style={{ width: '220px', height: '220px', display: 'block' }}
              />
            </div>

            <div style={{ fontSize: '12px', color: '#38BDF8', wordBreak: 'break-all', marginBottom: '20px' }}>
              {getShortUrl(qrModalLink)}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() =>
                  handleCopy(getShortUrl(qrModalLink), 'Short Link')
                }
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '10px',
                  backgroundColor: '#6366F1',
                  color: '#FFFFFF',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                Copy Link 📋
              </button>
              <button
                onClick={() => setQrModalLink(null)}
                style={{
                  padding: '10px 18px',
                  borderRadius: '10px',
                  backgroundColor: '#1E293B',
                  border: '1px solid #334155',
                  color: '#94A3B8',
                  fontWeight: '700',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 📈 DETAILS / STATS DRAWER MODAL */}
      {/* ========================================================================= */}
      {detailsModalLink && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 999,
            backgroundColor: 'rgba(0,0,0,0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '24px',
              padding: '28px',
              width: '100%',
              maxWidth: '650px',
              maxHeight: '85vh',
              overflowY: 'auto',
              color: '#F8FAFC',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '900', margin: 0 }}>
                  📈 {detailsModalLink.link?.post_name}
                </h3>
                <span style={{ color: '#94A3B8', fontSize: '12px' }}>
                  Platform: {detailsModalLink.link?.platform} | Product: {detailsModalLink.link?.product_name}
                </span>
              </div>
              <button
                onClick={() => setDetailsModalLink(null)}
                style={{
                  backgroundColor: '#1E293B',
                  border: 'none',
                  color: '#94A3B8',
                  borderRadius: '10px',
                  width: '32px',
                  height: '32px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                }}
              >
                ✕
              </button>
            </div>

            {/* Quick Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '10px', marginBottom: '20px' }}>
              <div style={{ backgroundColor: '#1E293B', padding: '12px 14px', borderRadius: '12px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '800' }}>Total Clicks</div>
                <div style={{ fontSize: '22px', fontWeight: '900', color: '#38BDF8', marginTop: '4px' }}>
                  {detailsModalLink.link?.total_clicks || 0}
                </div>
              </div>
              <div style={{ backgroundColor: '#1E293B', padding: '12px 14px', borderRadius: '12px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '800' }}>Unique Reach</div>
                <div style={{ fontSize: '22px', fontWeight: '900', color: '#10B981', marginTop: '4px' }}>
                  {detailsModalLink.link?.unique_clicks || 0}
                </div>
              </div>
              <div style={{ backgroundColor: '#1E293B', padding: '12px 14px', borderRadius: '12px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '800' }}>🤖 Android Installs</div>
                <div style={{ fontSize: '22px', fontWeight: '900', color: '#34D399', marginTop: '4px' }}>
                  {detailsModalLink.link?.android_downloads || 0}
                </div>
              </div>
              <div style={{ backgroundColor: '#1E293B', padding: '12px 14px', borderRadius: '12px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '800' }}>🍏 iOS Installs</div>
                <div style={{ fontSize: '22px', fontWeight: '900', color: '#38BDF8', marginTop: '4px' }}>
                  {detailsModalLink.link?.ios_downloads || 0}
                </div>
              </div>
              <div style={{ backgroundColor: '#1E293B', padding: '12px 14px', borderRadius: '12px', border: '1px solid #334155' }}>
                <div style={{ fontSize: '10px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '800' }}>Total Conv. %</div>
                <div style={{ fontSize: '22px', fontWeight: '900', color: '#C084FC', marginTop: '4px' }}>
                  {detailsModalLink.link?.total_clicks > 0
                    ? `${(((detailsModalLink.link?.total_downloads || 0) / detailsModalLink.link.total_clicks) * 100).toFixed(1)}%`
                    : '0.0%'}
                </div>
              </div>
            </div>

            {/* Recent Verified App Installs */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h4 style={{ fontSize: '14px', fontWeight: '800', margin: 0, color: '#CBD5E1' }}>
                  📲 Recent Verified App Installs ({detailsModalLink.recent_installs?.length || 0})
                </h4>
                <button
                  onClick={() => openTestInstallModal(detailsModalLink.link)}
                  style={{
                    background: 'rgba(168, 85, 247, 0.2)',
                    border: '1px solid rgba(168, 85, 247, 0.4)',
                    color: '#D8B4FE',
                    borderRadius: '6px',
                    padding: '3px 10px',
                    fontSize: '11px',
                    fontWeight: '700',
                    cursor: 'pointer',
                  }}
                >
                  ⚡ Simulate Install Now
                </button>
              </div>
              <div style={{ backgroundColor: '#1E293B', borderRadius: '14px', padding: '12px', maxHeight: '180px', overflowY: 'auto' }}>
                {!detailsModalLink.recent_installs || detailsModalLink.recent_installs.length === 0 ? (
                  <div style={{ textAlign: 'center', color: '#64748B', padding: '20px', fontSize: '12px' }}>
                    No app installs attributed to this referral link yet. Click "⚡ Simulate Install Now" to test!
                  </div>
                ) : (
                  detailsModalLink.recent_installs.map((inst) => {
                    const isIos = inst.platform?.toLowerCase() === 'ios';
                    return (
                      <div
                        key={inst.id || inst._id}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '8px 0',
                          borderBottom: '1px solid #334155',
                          fontSize: '12px',
                        }}
                      >
                        <div>
                          <span style={{ fontWeight: '700', color: isIos ? '#38BDF8' : '#34D399' }}>
                            {isIos ? '🍏 iOS App Store Install' : '🤖 Android Play Store Install'} (v{inst.version || '1.0.0'})
                          </span>
                          <span
                            style={{
                              marginLeft: '8px',
                              fontSize: '10px',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              backgroundColor: 'rgba(255,255,255,0.08)',
                              color: '#94A3B8',
                            }}
                          >
                            {inst.attribution_method || (isIos ? 'ios_ip_match' : 'android_play_referrer')}
                          </span>
                          <span style={{ color: '#64748B', marginLeft: '8px' }}>
                            Dev: {inst.device_id ? inst.device_id.slice(0, 10) + '...' : 'Unknown'}
                          </span>
                        </div>
                        <div style={{ color: '#94A3B8', fontSize: '11px' }}>
                          {new Date(inst.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                          {new Date(inst.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <h4 style={{ fontSize: '14px', fontWeight: '800', margin: '0 0 10px 0', color: '#CBD5E1' }}>
              ⚡ Recent Click Events
            </h4>
            <div style={{ backgroundColor: '#1E293B', borderRadius: '14px', padding: '12px', maxHeight: '240px', overflowY: 'auto' }}>
              {detailsModalLink.recent_clicks?.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#64748B', padding: '20px', fontSize: '12px' }}>
                  No click events recorded yet.
                </div>
              ) : (
                detailsModalLink.recent_clicks?.map((c) => (
                  <div
                    key={c.id || c._id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '8px 0',
                      borderBottom: '1px solid #334155',
                      fontSize: '12px',
                    }}
                  >
                    <div>
                      <span style={{ fontWeight: '700', color: '#F1F5F9' }}>
                        {c.device_type === 'Mobile' ? '📱 Mobile' : '💻 Desktop'} ({c.browser})
                      </span>
                      <span style={{ color: '#64748B', marginLeft: '8px' }}>OS: {c.os}</span>
                    </div>
                    <div style={{ color: '#94A3B8', fontSize: '11px' }}>
                      {new Date(c.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ⚡ MODAL: Real-Time App Install Telemetry Simulator */}
      {/* ========================================================================= */}
      {testInstallModalLink && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1000,
            backgroundColor: 'rgba(0,0,0,0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#0F172A',
              border: '1px solid #334155',
              borderRadius: '24px',
              padding: '28px',
              width: '100%',
              maxWidth: '560px',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: '0 25px 80px rgba(0,0,0,0.8)',
              color: '#F8FAFC',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '900', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  ⚡ Simulate App Install Telemetry
                </h3>
                <p style={{ color: '#94A3B8', fontSize: '12px', margin: '4px 0 0 0' }}>
                  Test real-time conversion for referral link: <strong style={{ color: '#38BDF8' }}>/r/{testInstallModalLink.slug}</strong>
                </p>
              </div>
              <button
                onClick={() => setTestInstallModalLink(null)}
                style={{
                  backgroundColor: '#1E293B',
                  border: 'none',
                  color: '#94A3B8',
                  borderRadius: '10px',
                  width: '32px',
                  height: '32px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                }}
              >
                ✕
              </button>
            </div>

            {/* Target Campaign Overview Pill */}
            <div
              style={{
                backgroundColor: '#1E293B',
                borderRadius: '12px',
                padding: '12px 16px',
                border: '1px solid #334155',
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '700' }}>
                  Campaign & Post
                </div>
                <div style={{ fontSize: '13px', fontWeight: '800', color: '#FFFFFF', marginTop: '2px' }}>
                  {testInstallModalLink.post_name} ({testInstallModalLink.campaign_name})
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '700' }}>
                  Current Downloads
                </div>
                <div style={{ fontSize: '13px', fontWeight: '800', color: '#A855F7', marginTop: '2px' }}>
                  🤖 {testInstallModalLink.android_downloads || 0} | 🍏 {testInstallModalLink.ios_downloads || 0} (Total: {testInstallModalLink.total_downloads || 0})
                </div>
              </div>
            </div>

            <form onSubmit={handleSimulateInstall}>
              {/* Platform Selector */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '8px' }}>
                  1. Operating System / Platform
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div
                    onClick={() => {
                      setInstallPlatform('android');
                      setInstallReferrerCustom(`utm_source=referral&slug=${testInstallModalLink.slug}&utm_content=mobile`);
                    }}
                    style={{
                      padding: '12px',
                      borderRadius: '12px',
                      backgroundColor: installPlatform === 'android' ? 'rgba(16, 185, 129, 0.15)' : '#1E293B',
                      border: `2px solid ${installPlatform === 'android' ? '#10B981' : '#334155'}`,
                      cursor: 'pointer',
                      textAlign: 'center',
                      fontWeight: '800',
                      color: installPlatform === 'android' ? '#34D399' : '#94A3B8',
                      fontSize: '13px',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    🤖 Android (Play Store)
                  </div>
                  <div
                    onClick={() => setInstallPlatform('ios')}
                    style={{
                      padding: '12px',
                      borderRadius: '12px',
                      backgroundColor: installPlatform === 'ios' ? 'rgba(56, 189, 248, 0.15)' : '#1E293B',
                      border: `2px solid ${installPlatform === 'ios' ? '#38BDF8' : '#334155'}`,
                      cursor: 'pointer',
                      textAlign: 'center',
                      fontWeight: '800',
                      color: installPlatform === 'ios' ? '#38BDF8' : '#94A3B8',
                      fontSize: '13px',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    🍏 iOS (App Store)
                  </div>
                </div>
              </div>

              {/* Platform Specific Explanation */}
              <div
                style={{
                  backgroundColor: installPlatform === 'android' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(56, 189, 248, 0.08)',
                  border: `1px solid ${installPlatform === 'android' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(56, 189, 248, 0.25)'}`,
                  borderRadius: '10px',
                  padding: '10px 14px',
                  marginBottom: '16px',
                  fontSize: '12px',
                  color: installPlatform === 'android' ? '#A7F3D0' : '#BAE6FD',
                }}
              >
                {installPlatform === 'android' ? (
                  <span>
                    <strong>Android Attribution:</strong> Simulates Google Play Install Referrer API returning campaign parameter <code>slug={testInstallModalLink.slug}</code> from the Play Store install receiver.
                  </span>
                ) : (
                  <span>
                    <strong>iOS Attribution:</strong> Simulates iOS App launch telemetry with probabilistic IP matching and direct referral code attribution for <code>{testInstallModalLink.slug}</code>.
                  </span>
                )}
              </div>

              {/* Device ID and App Version */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                    Unique Device ID
                  </label>
                  <input
                    type="text"
                    required
                    value={installDeviceId}
                    onChange={(e) => setInstallDeviceId(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      backgroundColor: '#1E293B',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#FFFFFF',
                      fontSize: '12px',
                      fontFamily: 'monospace',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                    App Version
                  </label>
                  <input
                    type="text"
                    required
                    value={installAppVersion}
                    onChange={(e) => setInstallAppVersion(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      backgroundColor: '#1E293B',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#FFFFFF',
                      fontSize: '12px',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              </div>

              {/* Android Specific: Referrer Payload */}
              {installPlatform === 'android' && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                    Google Play Install Referrer String
                  </label>
                  <input
                    type="text"
                    value={installReferrerCustom}
                    onChange={(e) => setInstallReferrerCustom(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      backgroundColor: '#1E293B',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#FFFFFF',
                      fontSize: '12px',
                      fontFamily: 'monospace',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              )}

              {/* iOS Specific: Client IP */}
              {installPlatform === 'ios' && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '800', color: '#94A3B8', textTransform: 'uppercase', marginBottom: '6px' }}>
                    Client IP Address (for IP Attribution Match)
                  </label>
                  <input
                    type="text"
                    value={installClientIp}
                    onChange={(e) => setInstallClientIp(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      backgroundColor: '#1E293B',
                      border: '1px solid #334155',
                      borderRadius: '10px',
                      color: '#FFFFFF',
                      fontSize: '12px',
                      fontFamily: 'monospace',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>
              )}

              {/* Result feedback */}
              {installTestResult && (
                <div
                  style={{
                    padding: '12px 16px',
                    borderRadius: '12px',
                    backgroundColor: installTestResult.ok ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    border: `1px solid ${installTestResult.ok ? '#10B981' : '#EF4444'}`,
                    color: installTestResult.ok ? '#34D399' : '#F87171',
                    fontSize: '12px',
                    marginBottom: '16px',
                  }}
                >
                  {installTestResult.ok ? (
                    <div>
                      <div style={{ fontWeight: '800', fontSize: '13px', marginBottom: '4px' }}>
                        🎉 Install Successfully Attributed in Real-Time!
                      </div>
                      <div>Attribution Method: <strong>{installTestResult.data?.attribution_method || 'verified'}</strong></div>
                      <div>Platform: <strong>{installTestResult.data?.platform?.toUpperCase()}</strong></div>
                      <div style={{ marginTop: '4px', fontWeight: '700' }}>
                        Updated Link Downloads: 🤖 {installTestResult.data?.android_downloads ?? installTestResult.data?.link?.android_downloads ?? 0} Android | 🍏 {installTestResult.data?.ios_downloads ?? installTestResult.data?.link?.ios_downloads ?? 0} iOS (Total: {installTestResult.data?.total_downloads ?? installTestResult.data?.link?.total_downloads ?? 0})
                      </div>
                    </div>
                  ) : (
                    <div>
                      <strong>Simulation Failed:</strong> {installTestResult.error || JSON.stringify(installTestResult.data)}
                    </div>
                  )}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmittingInstall}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '12px',
                  background: installPlatform === 'android'
                    ? 'linear-gradient(135deg, #10B981 0%, #059669 100%)'
                    : 'linear-gradient(135deg, #38BDF8 0%, #0284C7 100%)',
                  border: 'none',
                  color: '#FFFFFF',
                  fontWeight: '800',
                  fontSize: '13px',
                  cursor: isSubmittingInstall ? 'not-allowed' : 'pointer',
                  boxShadow: installPlatform === 'android'
                    ? '0 8px 25px rgba(16, 185, 129, 0.35)'
                    : '0 8px 25px rgba(56, 189, 248, 0.35)',
                }}
              >
                {isSubmittingInstall
                  ? 'Sending Install Telemetry...'
                  : `🚀 Send Real ${installPlatform === 'android' ? 'Android' : 'iOS'} Install Telemetry`}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketingCampaignsTab;
