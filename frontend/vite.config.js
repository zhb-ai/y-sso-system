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
        // target: 'http://192.168.50.71:8000',
        target: 'http://localhost:8000',
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
    minify: 'esbuild',
    emptyOutDir: true,  // 构建前清空输出目录
    cssCodeSplit: true,
    sourcemap: false,
    // 代码分割优化
    rollupOptions: {
      output: {
        // 手动代码分割策略
        manualChunks(id) {
          // Element Plus 单独打包
          if (id.includes('element-plus') || id.includes('@element-plus/icons-vue')) {
            return 'element-plus'
          }
          // Vue 核心库
          if (id.includes('vue') || id.includes('vue-router') || id.includes('pinia')) {
            return 'vue-core'
          }
          // 工具库
          if (id.includes('axios') || id.includes('crypto-js')) {
            return 'utils'
          }
        },
        // 资源文件命名规则
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          // 处理 name 可能为 undefined 的情况
          const name = assetInfo.name || ''
          const info = name.split('.')
          const ext = info[info.length - 1]
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(name)) {
            return 'assets/images/[name]-[hash][extname]'
          }
          if (/\.(css)$/i.test(name)) {
            return 'assets/css/[name]-[hash][extname]'
          }
          return 'assets/[name]-[hash][extname]'
        }
      }
    },
    // 压缩选项
    target: 'es2015',
    // 启用 brotli 压缩
    reportCompressedSize: false,
    // 调整 chunk 大小警告限制为 2MB
    chunkSizeWarningLimit: 2048
  },
  // 后端将静态文件挂载在根路径，资源使用相对路径加载
  // base: '/'
})
