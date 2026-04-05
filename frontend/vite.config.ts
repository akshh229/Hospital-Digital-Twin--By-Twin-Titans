import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxyTarget = process.env.VITE_PROXY_TARGET?.trim() || 'http://localhost:8000'
const wsProxyTarget =
  process.env.VITE_WS_PROXY_TARGET?.trim() ||
  apiProxyTarget.replace(/^http/i, (match) => (match.toLowerCase() === 'https' ? 'wss' : 'ws'))

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
      '/ws': {
        target: wsProxyTarget,
        ws: true,
      },
      '/health': {
        target: apiProxyTarget,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
