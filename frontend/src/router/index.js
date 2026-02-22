import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

// 公共路由
const publicRoutes = [
  // 测试页
  {
    path: '/test',
    name: 'test',
    component: () => import('../Test.vue'),
    meta: {
      title: '测试页面'
    }
  },
  // 统一登录页
  {
    path: '/login',
    name: 'login',
    component: () => import('../pages/Login.vue'),
    meta: {
      title: '统一登录'
    }
  },
  // 单点登录门户 / OAuth2 授权页
  {
    path: '/sso/login',
    name: 'ssoLogin',
    component: () => import('../pages/SSOLogin.vue'),
    meta: {
      title: '应用门户',
      isSSOLogin: true,
    }
  },
  // 兼容旧路径：/admin/login → /login
  {
    path: '/admin/login',
    redirect: '/login'
  },
  {
    path: '/404',
    name: '404',
    component: () => import('../pages/404.vue'),
    meta: {
      title: '404页面'
    }
  }
]

// 私有路由（管理后台，仅管理员可访问）
const privateRoutes = [
  {
    path: '/',
    name: 'layout',
    component: () => import('../layout/Layout.vue'),
    redirect: '/dashboard',
    meta: { requiresAdmin: true },
    children: [
      {
        path: '/dashboard',
        name: 'dashboard',
        component: () => import('../pages/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          requiresAdmin: true,
        }
      },
      // 系统管理
      {
        path: '/applications',
        name: 'applications',
        component: () => import('../pages/applications/Index.vue'),
        meta: {
          title: '应用管理',
          requiresAdmin: true,
        }
      },
      // 用户管理
      {
        path: '/users',
        name: 'users',
        component: () => import('../pages/users/Index.vue'),
        meta: {
          title: '用户管理',
          requiresAdmin: true,
        }
      },
      {
        path: '/users/:id',
        name: 'userEdit',
        component: () => import('../pages/users/Edit.vue'),
        meta: {
          title: '编辑用户',
          parent: 'users',
          requiresAdmin: true,
        }
      },
      // 角色权限管理
      {
        path: '/roles',
        name: 'roles',
        component: () => import('../pages/roles/Index.vue'),
        meta: {
          title: '角色管理',
          requiresAdmin: true,
        }
      },
      // SSO 角色管理
      {
        path: '/sso-roles',
        name: 'ssoRoles',
        component: () => import('../pages/sso-roles/Index.vue'),
        meta: {
          title: 'SSO 角色管理',
          requiresAdmin: true,
        }
      },
      // 组织架构管理
      {
        path: '/organization',
        name: 'organization',
        component: () => import('../pages/organization/Index.vue'),
        meta: {
          title: '组织架构',
          requiresAdmin: true,
        }
      },
      {
        path: '/departments',
        name: 'departments',
        component: () => import('../pages/departments/Index.vue'),
        meta: {
          title: '部门管理',
          requiresAdmin: true,
        }
      },
      {
        path: '/employees',
        name: 'employees',
        component: () => import('../pages/employees/Index.vue'),
        meta: {
          title: '员工管理',
          requiresAdmin: true,
        }
      },
      // 系统设置
      {
        path: '/settings',
        name: 'settings',
        component: () => import('../pages/settings/Index.vue'),
        meta: {
          title: '系统设置',
          requiresAdmin: true,
        }
      },
      {
        path: '/cache',
        name: 'cache',
        component: () => import('../pages/cache/Index.vue'),
        meta: {
          title: '缓存管理',
          requiresAdmin: true,
        }
      },
      // 个人资料
      {
        path: '/profile',
        name: 'profile',
        component: () => import('../pages/profile/Index.vue'),
        meta: {
          title: '个人资料',
          requiresAdmin: true,
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...publicRoutes, ...privateRoutes]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 尝试恢复认证状态（仅在首次访问时）
  if (!authStore.token && !authStore.userInfo) {
    authStore.restoreAuthState()
  }
  
  // 设置页面标题（从站点信息 Store 动态获取系统名称）
  const { useSiteStore } = await import('../stores/site')
  const siteStore = useSiteStore()
  const siteName = siteStore.systemName || '单点登录系统'
  document.title = to.meta.title ? `${to.meta.title} - ${siteName}` : siteName
  
  // 已登录用户访问 /login → 跳转到门户页
  // 注意：/sso/login 始终放行（门户模式 + OAuth2 授权流程都需要）
  if (to.path === '/login' && authStore.isLoggedIn) {
    next('/sso/login')
    return
  }
  
  // 公共路由直接放行
  const isPublicRoute = publicRoutes.some(route => route.path === to.path) || to.meta.isSSOLogin
  if (isPublicRoute) {
    next()
    return
  }
  
  // 非公共路由：检查是否登录
  if (!authStore.isLoggedIn) {
    next('/login')
    return
  }
  
  // 管理后台路由：检查管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    ElMessage.warning('权限不足，仅管理员可访问管理后台')
    next('/sso/login')
    return
  }
  
  next()
})

export default router