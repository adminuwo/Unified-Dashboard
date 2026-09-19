/**
 * Unified Dashboard API Configuration
 * 
 * Automatically loads backend API base URL from Vite environment variables:
 * - VITE_API_URL (Primary)
 * - VITE_API_BASE_URL (Alternative)
 * - window.__ENV__.VITE_API_URL (Runtime override)
 * 
 * Falls back to 'https://uwo24.com' in production or relative '/api' if not specified.
 */

const rawBaseUrl = 
  (typeof import.meta !== 'undefined' && import.meta.env && (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL)) ||
  (typeof window !== 'undefined' && window.__ENV__ && (window.__ENV__.VITE_API_URL || window.__ENV__.BACKEND_API_URL)) ||
  'https://uwo24.com';

// Clean trailing slashes
export const API_BASE_URL = (rawBaseUrl || '').replace(/\/+$/, '');

/**
 * Builds full API endpoint URL from relative path using backend API base URL.
 * @param {string} endpoint - Relative endpoint path (e.g. '/api/admin/login')
 * @returns {string} - Resolved target URL
 */
export const getApiUrl = (endpoint = '') => {
  if (!endpoint) return API_BASE_URL;

  // If already absolute URL, return as-is
  if (/^https?:\/\//i.test(endpoint)) {
    return endpoint;
  }

  const cleanPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  if (!API_BASE_URL) {
    return cleanPath;
  }

  // Prevent double '/api/api' if API_BASE_URL ends with '/api' and cleanPath starts with '/api'
  if (API_BASE_URL.endsWith('/api') && cleanPath.startsWith('/api')) {
    return `${API_BASE_URL.slice(0, -4)}${cleanPath}`;
  }

  return `${API_BASE_URL}${cleanPath}`;
};

/**
 * Enhanced fetch wrapper that automatically prefixes endpoints with API_BASE_URL
 */
export const apiFetch = async (endpoint, options = {}) => {
  const url = getApiUrl(endpoint);
  return fetch(url, options);
};

/**
 * Automatically intercepts global fetch calls to relative '/api/...' endpoints
 * and prefixes them with the environment-configured backend API base URL.
 */
export const initApiInterceptor = () => {
  if (typeof window === 'undefined' || window._apiInterceptorInitialized) return;

  const originalFetch = window.fetch.bind(window);

  window.fetch = async (input, init) => {
    try {
      if (typeof input === 'string') {
        if (input.startsWith('/api/') || input === '/api') {
          input = getApiUrl(input);
        }
      } else if (input && typeof input === 'object' && input.url) {
        try {
          const urlObj = new URL(input.url, window.location.origin);
          if (urlObj.pathname.startsWith('/api')) {
            const resolved = getApiUrl(urlObj.pathname + urlObj.search);
            input = new Request(resolved, input);
          }
        } catch (e) {
          // Ignore invalid URL parse
        }
      }
    } catch (err) {
      console.warn('[API Interceptor] Failed to transform URL:', err);
    }

    return originalFetch(input, init);
  };

  window._apiInterceptorInitialized = true;
  console.log(`[API Config] Initialized with Backend API Base: ${API_BASE_URL || '(relative proxy)'}`);
};
