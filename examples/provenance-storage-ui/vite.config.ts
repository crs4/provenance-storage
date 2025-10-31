import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/status': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/query':  'http://localhost:8000',
      '/get':    'http://localhost:8000',
    }
  }
})
