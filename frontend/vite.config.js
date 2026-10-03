import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // './' suits GitHub Pages; the container build sets VITE_BASE=/ so deep links find /assets/...
  base: process.env.VITE_BASE || './',
})
