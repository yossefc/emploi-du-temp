import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// Simple, working Vite configuration
export default defineConfig({
  plugins: [react()],
  
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/components'),
      '@hooks': resolve(__dirname, './src/hooks'),
      '@utils': resolve(__dirname, './src/utils'),
      '@pages': resolve(__dirname, './src/pages'),
    },
  },
  
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  
  build: {
    target: 'es2015',
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
  },
  
  esbuild: {
    target: 'es2020',
  },
});