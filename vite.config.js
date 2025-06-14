import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    assetsInlineLimit: 4096,
    manifest: true,
    outDir: resolve('./brownsea/static/dist'),
    rollupOptions: {
      input: {
        main: resolve('./brownsea/static_src/main.ts'),
        css: resolve('./brownsea/static_src/scss/main.scss')
      },
    }
  },
  server: {
    port: 5173,
    strictPort: true,
    host: true,
  },
  base: '/static/dist/',
}) 