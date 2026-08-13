import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const UWOLoginModal = ({ isOpen, onClose, onSuccess, appCode = "aisa", apiKey = "key_aisa_live_master_2026" }) => {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      if (isRegisterMode) {
        // 1. Register new central account
        const regRes = await fetch('http://localhost:8000/api/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Application-Key': apiKey,
          },
          body: JSON.stringify({ name, email, password }),
        });

        const regData = await regRes.json();
        if (!regRes.ok) {
          throw new Error(regData.detail || 'Registration failed');
        }

        setSuccessMsg('Account created successfully! Signing in...');
      }

      // 2. Authenticate & Obtain Tokens
      const loginRes = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Application-Key': apiKey,
        },
        body: JSON.stringify({ email, password }),
      });

      const loginData = await loginRes.json();

      if (!loginRes.ok) {
        throw new Error(loginData.detail || 'Authentication failed');
      }

      // Store tokens and identity
      if (loginData.access_token) {
        localStorage.setItem('uwo_access_token', loginData.access_token);
        localStorage.setItem('uwo_user', JSON.stringify(loginData.user));
      }

      setLoading(false);
      onSuccess(loginData);
      onClose();
    } catch (err) {
      setLoading(false);
      setError(err.message || 'Authentication error');
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-slate-950/75 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 15 }}
          className="relative w-full max-w-md p-6 bg-slate-900/95 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-xl">
                ⚡
              </div>
              <div>
                <h3 className="text-base font-black text-white uppercase tracking-wider">
                  {isRegisterMode ? 'Create UWO Account' : 'UWO SSO Sign In'}
                </h3>
                <p className="text-xs text-slate-400">Unified Web Options Identity Platform</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Mode Switcher Tabs */}
          <div className="flex p-1 mt-4 bg-slate-950/70 border border-slate-800 rounded-xl">
            <button
              type="button"
              onClick={() => { setIsRegisterMode(false); setError(''); setSuccessMsg(''); }}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                !isRegisterMode
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsRegisterMode(true); setError(''); setSuccessMsg(''); }}
              className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
                isRegisterMode
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
            {error && (
              <div className="p-3 text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl">
                {error}
              </div>
            )}

            {successMsg && (
              <div className="p-3 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                {successMsg}
              </div>
            )}

            {isRegisterMode && (
              <div>
                <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Sanskar Sharma"
                  className="w-full px-4 py-2.5 text-sm bg-slate-950/60 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            )}

            <div>
              <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="sanskar@uwo24.com"
                className="w-full px-4 py-2.5 text-sm bg-slate-950/60 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 text-sm bg-slate-950/60 border border-slate-800 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 mt-1 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-bold text-sm tracking-wide shadow-lg shadow-indigo-500/25 hover:from-indigo-600 hover:to-purple-700 transition-all disabled:opacity-50"
            >
              {loading
                ? isRegisterMode ? 'Creating Account...' : 'Authenticating...'
                : isRegisterMode ? 'Register & Sign In' : 'Sign In with UWO'}
            </button>
          </form>

          {/* Footer toggle note */}
          <div className="mt-4 pt-3 border-t border-slate-800 text-center text-xs text-slate-400">
            {isRegisterMode ? (
              <span>Already have a UWO account? <button type="button" onClick={() => setIsRegisterMode(false)} className="text-indigo-400 font-bold hover:underline">Sign In</button></span>
            ) : (
              <span>New to UWO Platform? <button type="button" onClick={() => setIsRegisterMode(true)} className="text-indigo-400 font-bold hover:underline">Create an Account</button></span>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default UWOLoginModal;
