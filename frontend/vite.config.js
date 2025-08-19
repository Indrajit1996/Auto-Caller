import react from '@vitejs/plugin-react';
import dotenv from 'dotenv';
import path from 'path';
import { defineConfig } from 'vite';

// Load environment variables in the correct order
dotenv.config({ path: path.resolve(__dirname, '../.env') });

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    extensions: ['.js', '.jsx'],
  },
  plugins: [react()],
  server: {
    proxy: {
      '/api': process.env.VITE_API_URL_DEV,
    },
  },
  watchOptions: {
    ignored: ['**/node_modules/**', '**/dist/**'],
  },
});
