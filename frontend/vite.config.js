import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5200,
    /** 设置 host: true 才可以使用 Network 的形式，以 IP 访问项目 */
    host: true, // host: "0.0.0.0"
     /** 是否自动打开浏览器 */
    open: false,
     /** 跨域设置允许 */
    cors: true,
    /** 端口被占用时，是否直接退出 */
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://192.168.50.71:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },
  // 设置输出目录为后端的 web 文件夹, js,css 静态资源 assets
  build: {
    outDir: path.resolve(__dirname, '../web'),
    assetsDir: 'assets',
    minify: false,
    emptyOutDir: true,  // 构建前清空输出目录
  },
  // 后端将静态文件挂载在根路径，资源使用相对路径加载
  // base: '/'
})
