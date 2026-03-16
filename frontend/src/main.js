import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/themes.css'
import './styles/index.css'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 在应用启动时恢复认证状态
const authStore = useAuthStore()
authStore.restoreAuthState()

// 预加载站点信息（系统名称、描述等）
import { useSiteStore } from './stores/site'
const siteStore = useSiteStore()
siteStore.load()

// 挂载应用
app.mount('#app')