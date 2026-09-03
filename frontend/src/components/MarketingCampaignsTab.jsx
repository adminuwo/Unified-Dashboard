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

  const fetchData = async () => {
    try {
      setLoading(true);
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
    } catch (err) {
      console.error('Error fetching marketing telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

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
    <div className="marketing-tab-container" style={{ padding: '24px', color: '#F8FAFC' }}>
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

      {/* KPI Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '18px',
          marginBottom: '28px',
        }}
      >
        {/* Total Clicks */}
        <div
          style={{
            backgroundColor: '#0F172A',
            border: '1px solid #1E293B',
            borderRadius: '18px',
            padding: '20px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Total Referral Clicks
            </span>
            <span style={{ fontSize: '20px' }}>🖱️</span>
          </div>
          <div style={{ fontSize: '32px', fontWeight: '900', color: '#38BDF8', marginTop: '10px' }}>
            {summary?.total_clicks?.toLocaleString() || '0'}
          </div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '6px' }}>
            Across {summary?.total_links || links.length} active campaigns
          </div>
        </div>

        {/* Unique Reach */}
        <div
          style={{
            backgroundColor: '#0F172A',
            border: '1px solid #1E293B',
            borderRadius: '18px',
            padding: '20px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Unique Audience Reach
            </span>
            <span style={{ fontSize: '20px' }}>👥</span>
          </div>
          <div style={{ fontSize: '32px', fontWeight: '900', color: '#10B981', marginTop: '10px' }}>
            {summary?.unique_reach?.toLocaleString() || '0'}
          </div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '6px' }}>
            Unique individuals visiting via links
          </div>
        </div>

        {/* Top Performing Post */}
        <div
          style={{
            backgroundColor: '#0F172A',
            border: '1px solid #1E293B',
            borderRadius: '18px',
            padding: '20px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Best Performing Post
            </span>
            <span style={{ fontSize: '20px' }}>🏆</span>
          </div>
          <div
            style={{
              fontSize: '18px',
              fontWeight: '900',
              color: '#F59E0B',
              marginTop: '10px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {summary?.top_post?.post_name || 'No post data yet'}
          </div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '6px' }}>
            {summary?.top_post ? `${summary.top_post.total_clicks} clicks (${summary.top_post.platform})` : 'Start a campaign to view'}
          </div>
        </div>

        {/* Top Platform */}
        <div
          style={{
            backgroundColor: '#0F172A',
            border: '1px solid #1E293B',
            borderRadius: '18px',
            padding: '20px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#94A3B8' }}>
            <span style={{ fontSize: '12px', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Top Channel
            </span>
            <span style={{ fontSize: '20px' }}>📱</span>
          </div>
          <div style={{ fontSize: '22px', fontWeight: '900', color: '#EC4899', marginTop: '10px' }}>
            {summary?.top_platform ? `${summary.top_platform.icon} ${summary.top_platform.name}` : 'No traffic yet'}
          </div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '6px' }}>
            {summary?.top_platform ? `${summary.top_platform.clicks} clicks (${summary.top_platform.share_pct}%)` : 'Ready for tracking'}
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
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ backgroundColor: '#1E293B', color: '#94A3B8', borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Post / Campaign Name</th>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Product</th>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Platform</th>
                <th style={{ padding: '14px 18px', fontWeight: '800' }}>Short Redirect URL</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Total Clicks</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Unique Reach</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'center' }}>Status</th>
                <th style={{ padding: '14px 18px', fontWeight: '800', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ padding: '40px', textAlign: 'center', color: '#94A3B8' }}>
                    Loading marketing links...
                  </td>
                </tr>
              ) : filteredLinks.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ padding: '40px', textAlign: 'center', color: '#94A3B8' }}>
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
                            onClick={() => handleCopy(link.short_url || `${window.location.origin}/r/${link.slug}`, 'Short link')}
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
                            onClick={() => openDetails(link)}
                            title="View Click Telemetry"
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
                    const shortUrl = resLink.short_url || `${window.location.origin}/r/${resLink.slug}`;
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
                  qrModalLink.short_url || `${window.location.origin}/r/${qrModalLink.slug}`
                )}`}
                alt="QR Code"
                style={{ width: '220px', height: '220px', display: 'block' }}
              />
            </div>

            <div style={{ fontSize: '12px', color: '#38BDF8', wordBreak: 'break-all', marginBottom: '20px' }}>
              {qrModalLink.short_url || `${window.location.origin}/r/${qrModalLink.slug}`}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() =>
                  handleCopy(qrModalLink.short_url || `${window.location.origin}/r/${qrModalLink.slug}`, 'Short Link')
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
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
              <div style={{ backgroundColor: '#1E293B', padding: '14px', borderRadius: '12px' }}>
                <div style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '800' }}>Total Clicks</div>
                <div style={{ fontSize: '24px', fontWeight: '900', color: '#38BDF8', marginTop: '4px' }}>
                  {detailsModalLink.link?.total_clicks}
                </div>
              </div>
              <div style={{ backgroundColor: '#1E293B', padding: '14px', borderRadius: '12px' }}>
                <div style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: '800' }}>Unique People Reach</div>
                <div style={{ fontSize: '24px', fontWeight: '900', color: '#10B981', marginTop: '4px' }}>
                  {detailsModalLink.link?.unique_clicks}
                </div>
              </div>
            </div>

            {/* Recent Live Click Events */}
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
    </div>
  );
};

export default MarketingCampaignsTab;
