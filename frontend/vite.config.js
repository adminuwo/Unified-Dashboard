import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    base: './',

    server: {
      port: 5174,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || env.VITE_PROXY_TARGET || 'https://uwo24.com',
          changeOrigin: true,
        },
      },
    },
  };
});

