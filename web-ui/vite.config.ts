import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [vue()],
  base: './',
  build: {
    outDir: './release',
    emptyOutDir: true,
    minify: mode === 'production',
    sourcemap: mode === 'development',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5890,
    open: true,
    host: '0.0.0.0',
    proxy: {
      '/browser': {
        /**
         * comfyUI 服务端地址
         */
        target: process.env.COMFYUI_SERVER_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
}))
