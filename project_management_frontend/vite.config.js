import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Vite 7.x configuration optimized for Node.js 22+
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      minify: 'terser',
      // Updated target for modern browsers and Node.js 22+
      target: 'esnext',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router', 'pinia'],
            primevue: ['primevue'],
            gantt: ['dhtmlx-gantt'],
          },
        },
      },
      // Vite 7.x optimizations
      modulePreload: {
        polyfill: false, // Modern browsers support module preload natively
      },
      cssCodeSplit: true,
      assetsInlineLimit: 4096,
    },
    optimizeDeps: {
      include: ['vue', 'vue-router', 'pinia', 'primevue', 'axios'],
      // Vite 7.x uses esbuild by default for deps optimization
      esbuildOptions: {
        target: 'esnext',
      },
    },
    // Enable future-ready features
    css: {
      devSourcemap: true,
    },
    // Vite 7.x JSON handling
    json: {
      stringify: true,
    },
  }
})
