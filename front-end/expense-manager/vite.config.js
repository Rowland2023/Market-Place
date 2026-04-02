import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 1. FASTAPI (Invoice Service) 
      // Specific routes must always come BEFORE generic /api
      '/api/invoices': {
        target: 'http://invoice_service:8001',
        changeOrigin: true,
        secure: false,
      },

      // 2. NODE.JS (Employee Service)
      '/api/employees': {
        target: 'http://node_employee:3000',
        changeOrigin: true,
        secure: false,
      },

      // 3. DJANGO (Core Store)
      // This is the "catch-all". If the above don't match, it goes here.
      '/api': {
        target: 'http://django-backend:8000',
        changeOrigin: true,
        secure: false,
      },

      // 4. DJANGO STATIC ASSETS
      '/static': {
        target: 'http://django-backend:8000',
        changeOrigin: true,
      },
    }
  }
})