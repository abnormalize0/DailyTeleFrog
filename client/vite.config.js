const vue = require('@vitejs/plugin-vue');
import requireTransform from 'vite-plugin-require';
import { defineConfig } from "vite";
import path from 'path';

export default defineConfig({
  plugins: [
    vue(),
    requireTransform({
      fileRegex: /.js$|.vue$/
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    }
  }
});