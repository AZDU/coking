import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  // GitHub Pages 项目站点需要带仓库名前缀
  base: '/coking/',
  plugins: [vue()],
})
