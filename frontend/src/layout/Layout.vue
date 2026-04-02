<template>
  <div class="app-container">
    <!-- 移动端遮罩层 -->
    <div 
      :class="{ 'sidebar-overlay': true, 'active': isMobileMenuOpen }" 
      @click="closeMobileMenu"
    ></div>
    
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'sidebar-collapse': isCollapse, 'show': isMobileMenuOpen }">
      <div class="sidebar-header">
        <div class="logo">
          <el-icon class="logo-icon"><Connection /></el-icon>
          <span v-if="!isCollapse" class="logo-text">SSO系统</span>
        </div>
        <el-button
          circle
          class="collapse-btn"
          @click="toggleCollapse"
        >
          <el-icon>
            <component :is="isCollapse ? ArrowRight : ArrowLeft" />
          </el-icon>
        </el-button>
      </div>
      
      <!-- 侧边栏菜单 -->
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :collapse="isCollapse"
        router
      >
        <template v-for="menu in menuList" :key="menu.path">
          <!-- 没有子菜单 -->
          <el-menu-item v-if="!menu.children" :index="menu.path">
            <el-icon>
              <component :is="menu.icon" />
            </el-icon>
            <template #title>{{ menu.meta.title }}</template>
          </el-menu-item>
          
          <!-- 有子菜单 -->
          <el-sub-menu v-else :index="menu.path">
            <template #title>
              <el-icon>
                <component :is="menu.icon" />
              </el-icon>
              <span>{{ menu.meta.title }}</span>
            </template>
            
            <template v-for="subMenu in menu.children" :key="subMenu.path">
              <el-menu-item :index="subMenu.path">
                <el-icon>
                  <component :is="subMenu.icon" />
                </el-icon>
                <template #title>{{ subMenu.meta.title }}</template>
              </el-menu-item>
            </template>
          </el-sub-menu>
        </template>
      </el-menu>
    </aside>
    
    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 顶部导航 -->
      <header class="top-header">
        <div class="header-left">
          <el-button
            circle
            class="header-btn"
            @click="toggleCollapse"
          >
            <el-icon><IconMenu /></el-icon>
          </el-button>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRoute.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 应用授权按钮 -->
          <el-button 
            site="small"
            plain 
            class="header-action app-auth-btn"
            @click="handleAppAuthorization"
            title="应用授权"
          >
            <el-icon><Key /></el-icon>
            <span>应用授权</span>
          </el-button>
          
          <!-- 用户信息 -->
          <el-dropdown trigger="click" class="header-action user-info">
            <div class="user-avatar">
              <el-avatar :size="32">{{ userInitial }}</el-avatar>
              <span v-if="userInfo" class="user-name">{{ userInfo.username }}</span>
              <el-icon><arrow-down /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleProfile">个人资料</el-dropdown-item>
                <el-dropdown-item v-if="isAdmin" @click="handleSettings">系统设置</el-dropdown-item>
                <el-divider />
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 内容区域 -->
      <div class="content-wrapper">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
      
      <!-- 页脚 -->
      <footer class="app-footer">
        <div class="footer-content">
          <span>© {{ currentYear }} {{ siteStore.systemName }}</span>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
// 导入图标组件
import {
  DataAnalysis,
  Shop,
  User,
  Management,
  OfficeBuilding,
  Folder,
  Avatar,
  Setting,
  Key,
  Menu as IconMenu,
  ArrowLeft,
  ArrowRight,
  ArrowDown,
  Connection,
  Collection,
  DocumentCopy,
  UserFilled,
  Medal,
  Grid
} from '@element-plus/icons-vue'

import { useSiteStore } from '@/stores/site'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const siteStore = useSiteStore()

// 当前年份
const currentYear = new Date().getFullYear()

// 折叠状态
const isCollapse = ref(false)

// 移动端菜单显示状态
const isMobileMenuOpen = ref(false)

// 判断是否为移动端
const isMobile = () => window.innerWidth <= 768

// 切换折叠（桌面端）/ 切换菜单显示（移动端）
const toggleCollapse = () => {
  if (isMobile()) {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
  } else {
    isCollapse.value = !isCollapse.value
  }
}

// 关闭移动端菜单
const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

// 监听窗口大小变化，当切换到桌面端时关闭移动菜单
const handleResize = () => {
  if (!isMobile() && isMobileMenuOpen.value) {
    isMobileMenuOpen.value = false
  }
}

// 监听路由变化，导航时自动关闭移动端菜单
watch(() => route.path, () => {
  if (isMobileMenuOpen.value) {
    isMobileMenuOpen.value = false
  }
})

// 当前路由
const currentRoute = computed(() => route)

// 激活的菜单
const activeMenu = computed(() => {
  return route.path || '/dashboard'
})

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 用户首字母
const userInitial = computed(() => {
  if (userInfo.value && userInfo.value.username) {
    return userInfo.value.username.charAt(0).toUpperCase()
  }
  return 'U'
})

// 是否为管理员
const isAdmin = computed(() => {
  return authStore.isAdmin
})

// 菜单列表
const menuList = [
  {
    path: '/dashboard',
    name: 'dashboard',
    meta: { title: '仪表盘' },
    icon: DataAnalysis
  },
  // 系统管理
  {
    path: '/applications',
    name: 'applications',
    meta: { title: '应用管理' },
    icon: Grid
  },
  // 用户管理
  {
    path: '/users',
    name: 'users',
    meta: { title: '用户管理' },
    icon: User
  },
  // 角色权限管理
  {
    path: '/roles',
    name: 'roles',
    meta: { title: '角色管理' },
    icon: Medal
  },
  // SSO 角色管理
  {
    path: '/sso-roles',
    name: 'ssoRoles',
    meta: { title: 'SSO 角色' },
    icon: Connection
  },
  // 组织架构管理（直接访问，无子菜单）
  {
    path: '/organization',
    name: 'organization',
    meta: { title: '组织架构' },
    icon: OfficeBuilding
  },
  // 员工管理（独立菜单）
  {
    path: '/employees',
    name: 'employees',
    meta: { title: '员工管理' },
    icon: DocumentCopy
  },
  // 系统设置
  {
    path: '/settings',
    name: 'settings',
    meta: { title: '系统设置' },
    icon: Setting
  },
  // 缓存管理
  {
    path: '/cache',
    name: 'cache',
    meta: { title: '缓存管理' },
    icon: Collection
  }
]

// 退出登录
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
  ElMessage.success('退出登录成功')
}

// 个人中心
const handleProfile = () => {
  router.push('/profile')
}

// 设置
const handleSettings = () => {
  router.push('/settings')
}

// 应用授权
const handleAppAuthorization = () => {
  router.push('/sso/login')
}

// 初始化
onMounted(async () => {
  // 添加窗口大小监听
  window.addEventListener('resize', handleResize)
  
  // 获取当前用户信息
  if (authStore.isLoggedIn && !authStore.userInfo) {
    await authStore.getCurrentUser()
  }
  
  // 如果仍然没有用户信息但token存在，尝试恢复认证状态
  if (!authStore.userInfo && authStore.token) {
    const restored = authStore.restoreAuthState()
    if (!restored) {
      // 如果恢复失败，跳转到登录页
      router.push('/login')
    }
  }
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-large);
  height: 64px;
  border-bottom: 1px solid var(--border_color);
  background-color: var(--white);
}
.sidebar-collapse .sidebar-header {
  justify-content: center;
}


.sidebar-nav-item.active {
  background-color: rgba(var(--primary), 0.1);
  color: rgba(var(--primary), 1);
  border-right: 3px solid rgba(var(--primary), 1);
}
/* 移动端遮罩层 */
.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: calc(var(--z-fixed) - 1);
  backdrop-filter: blur(2px);
  transition: opacity 0.3s ease;
  opacity: 0;
  visibility: hidden;
}

.sidebar-overlay.active {
  opacity: 1;
  visibility: visible;
}

@media (max-width: 768px) {
  .sidebar-overlay {
    display: block;
  }
}

/* 侧边栏菜单特殊样式 */
.sidebar-menu {
  border-right: none;
  height: calc(100vh - 64px);
  overflow-y: auto;
  background: transparent;
  padding: 1rem 0;
}

.sidebar-menu::-webkit-scrollbar {
  width: 6px;
}

.sidebar-menu::-webkit-scrollbar-track {
  background: var(--light-gray);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background-color: var(--border_color);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background-color: rgba(var(--secondary), 0.5);
}

:deep(.el-menu) {
  border-right: none;
}
.sidebar-menu{
  border-right: none;
}


.sidebar-menu :deep(.el-menu-item) {
  margin: 4px 0.5rem;
  border-radius: 0.5rem;
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  font-weight: var(--el-font-weight-bold);
  transition: none; 
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  color: rgba(var(--primary), 1);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(var(--primary), 1);
  color: var(--white);
  box-shadow: var(--hover-shadow);
}

:deep(.el-menu-item .el-menu-tooltip__trigger) {
  padding: 0;
}
:deep(.el-sub-menu__title) {
  height: 50px;
  line-height: 50px;
  margin: 4px 0.5rem;
  border-radius: 0.5rem;
  transition: var(--app-transition);
  display: flex;
  align-items: center;
  padding: 0 1rem !important;
  color: var(--font-color) !important;
  font-weight: 500;
  font-size: 14px;
}

:deep(.el-sub-menu .el-menu-item) {
  margin: 0 0.5rem;
  padding-left: 2.5rem !important;
  height: 44px;
  line-height: 44px;
  border-radius: 0.375rem;
  background-color: var(--light-gray) !important;
  color: var(--font-color) !important;
  font-weight: var(--el-font-weight-medium);
  font-size: var(--el-font-size-sm);
}

:deep(.el-sub-menu .el-menu-item:hover) {
  background-color: rgba(var(--primary), 0.05) !important;
  color: rgba(var(--primary), 1) !important;
}

:deep(.el-sub-menu .el-menu-item.is-active) {
  background-color: rgba(var(--primary), 0.1) !important;
  color: rgba(var(--primary), 1) !important;
  font-weight: var(--el-font-weight-bold);
}

:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title .el-icon) {
  width: 20px;
  height: 20px;
  margin-right: 0.75rem;
  vertical-align: middle;
  flex-shrink: 0;
  font-size: var(--el-font-size-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: inherit;
}

:deep(.el-menu--collapse) {
  width: 68px;
}

:deep(.el-menu--collapse .el-menu-item),
:deep(.el-menu--collapse .el-sub-menu__title) {
  margin: 4px 8px;
  text-align: center;
  padding: 0 !important;
  justify-content: center;
}

:deep(.el-menu--collapse .el-menu-item .el-icon),
:deep(.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0;
  margin: 0 auto;
}

:deep(.el-menu--collapse .el-menu-item span),
:deep(.el-menu--collapse .el-sub-menu__title span) {
  height: 0;
  width: 0;
  overflow: hidden;
  visibility: hidden;
}

/* 展开时的菜单项 */
:deep(.el-menu--vertical:not(.el-menu--collapse) .el-menu-item span),
:deep(.el-menu--vertical:not(.el-menu--collapse) .el-sub-menu__title span) {
  height: auto;
  width: auto;
  overflow: visible;
  visibility: visible;
  flex-grow: 1;
  text-align: left;
  font-weight: var(--el-font-weight-bold);
}

/* 侧边栏折叠样式 */
.sidebar {
  transition: width 0.3s ease;
  background-color: var(--white);
  border-right: 1px solid var(--border_color);
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  width: 250px;
  z-index: var(--z-fixed);
  overflow-y: auto;
}

.sidebar.sidebar-collapse {
  width: 68px;
}

.sidebar.sidebar-collapse .logo-text {
  display: none;
}

/* 主内容区域适配 - 动态计算宽高 */
.main-content {
  margin-left: 250px;
  width: calc(100% - 250px);
  height: 100vh;
  transition: margin-left 0.3s ease, width 0.3s ease;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar.sidebar-collapse ~ .main-content {
  margin-left: 68px;
  width: calc(100% - 68px);
}

/* 内容区域 - 内部滚动 */
.content-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  height: calc(100vh - 64px);
  padding: 1.5rem;
  box-sizing: border-box;
}

/* 内容区域滚动条样式 */
.content-wrapper::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.content-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background-color: var(--border_color);
  border-radius: 4px;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background-color: rgba(var(--secondary), 0.5);
}

/* 页脚样式 - 底部居中 */
.app-footer {
  padding: 5px 1.5rem;
  flex-shrink: 0;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--font-light-color);
}

/* 应用授权按钮样式 */
.app-auth-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 头部右侧布局 */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .sidebar {
    width: 250px;
    transform: translateX(-100%);
  }

  .sidebar.show {
    transform: translateX(0);
  }

  .main-content {
    margin-left: 0;
  }

  /* 移动端应用授权按钮样式 */
  .app-auth-btn {
    font-size: 12px;
    padding: 0 12px;
  }

  .app-auth-btn span {
    display: none;
  }

  /* 移动端头部右侧布局 */
  .header-right {
    gap: 8px;
  }
}

</style>