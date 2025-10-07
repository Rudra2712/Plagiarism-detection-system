import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // Proxy /api requests to the backend Flask server running on port 5000.
    // Vite does not use the `proxy` field in package.json (that's a CRA convention),
    // so we configure it here explicitly.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        // Don't proxy websocket requests for these endpoints
        ws: false,
      },
    },
  },
})


