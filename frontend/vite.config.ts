import path from 'path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Proxy /api/v1 requests to the backend during dev so we avoid
// needing to worry about CORS in the browser dev environment.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // @/ maps to src/ — consistent with shadcn convention
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
