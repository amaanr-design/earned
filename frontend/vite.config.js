import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// GitHub Pages serves a project site under /<repo>/. Applied to `build` and
// `preview` only, so `npm run dev` stays at / and the launch config is unchanged.
const PAGES_BASE = '/earned/'

// https://vite.dev/config/
export default defineConfig(({ command, isPreview }) => ({
  base: command === 'build' || isPreview ? PAGES_BASE : '/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      // Registration lives in src/main.jsx via virtual:pwa-register.
      injectRegister: false,
      // Service worker is build-only; dev never registers one.
      devOptions: { enabled: false },
      manifest: {
        // start_url and scope default to `base`.
        name: 'Earned',
        short_name: 'Earned',
        description: 'Earned',
        display: 'standalone',
        theme_color: '#16171d',
        background_color: '#16171d',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        // App shell only: precache the build output, cache-first.
        globPatterns: ['**/*.{js,css,html,png,svg}'],
        // No runtimeCaching on purpose. API responses are never cached —
        // offline behaviour for cards is an open design question.
        navigateFallbackDenylist: [/^\/api\//],
        // A new build takes over immediately so a stale worker never serves
        // an old shell during development.
        skipWaiting: true,
        clientsClaim: true,
        cleanupOutdatedCaches: true,
      },
    }),
  ],
  server: {
    port: process.env.PORT ? Number(process.env.PORT) : 5173,
    proxy: {
      '/api': 'http://localhost:8001',
    },
  },
}))
