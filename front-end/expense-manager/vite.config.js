import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 1. NODE.JS (Employee Service)
      '/api/employees': {
        target: 'http://node_employee:3000',
        changeOrigin: true,
        secure: false,
      },

      // 2. FASTAPI (Invoice Service)
      '/api/invoices': {
        target: 'http://invoice_service:8001',
        changeOrigin: true,
        secure: false,
      },

      // 3. DJANGO (Core Store / Orchestrator)
      // This acts as the "catch-all" for any other /api requests
      '/api': {
        target: 'http://django_backend:8000',
        changeOrigin: true,
        secure: false,
      },

      // 4. DJANGO STATIC ASSETS
      '/static': {
        target: 'http://django_backend:8000',
        changeOrigin: true,
      },
    }
  }
})