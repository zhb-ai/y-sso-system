import axios from 'axios'
import { useAuthStore } from '../stores/auth'

// 创建axios实例
const api = axios.create({
  // baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 是否正在刷新 Token
let isRefreshing = false
// 等待刷新完成的请求队列
let refreshSubscribers = []

// 将请求添加到等待队列
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

// 刷新完成后，执行队列中的所有请求
function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

// 刷新失败，拒绝队列中的所有请求
function onRefreshFailed(error) {
  refreshSubscribers.forEach(callback => callback(null, error))
  refreshSubscribers = []
}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('发送HTTP请求:', config)
    const authStore = useAuthStore()
    // 添加Token
    if (authStore.token) {
      config.headers['Authorization'] = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// ==================== 辅助函数 ====================

// 登录页路径列表
const LOGIN_PAGES = ['/login', '/admin/login', '/sso/login']

// 跳转到登录页（避免重复跳转）
function redirectToLogin() {
  if (!LOGIN_PAGES.includes(window.location.pathname)) {
    window.location.href = '/login'
  }
}

// 从 BaseResponse 格式的错误响应中提取信息
function parseErrorResponse(responseData) {
  const errorCode = responseData?.error_code || ''
  let message = responseData?.message || ''
  // 附加详细信息
  if (responseData?.msg_details?.length > 0) {
    message += ': ' + responseData.msg_details.join(', ')
  }
  return { errorCode, message }
}

// 构造统一的错误对象
function createApiError(message, { errorCode = '', isNetworkError = false, isTimeoutError = false } = {}) {
  const err = new Error(message)
  err.errorCode = errorCode
  err.isNetworkError = isNetworkError
  err.isTimeoutError = isTimeoutError
  return err
}

// ==================== 响应拦截器 ====================

api.interceptors.response.use(
  (response) => {
    // 成功响应：解包 BaseResponse，直接返回 { status, message, data, ... }
    return response.data
  },
  async (error) => {
    const authStore = useAuthStore()
    const originalRequest = error.config

    // ---------- 无响应：网络错误 / 超时 ----------
    if (!error.response) {
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        return Promise.reject(createApiError('请求超时，请检查网络连接后重试', { isTimeoutError: true }))
      }
      return Promise.reject(createApiError('网络连接失败，请检查网络设置', { isNetworkError: true }))
    }

    // ---------- 有响应：从 BaseResponse 提取 error_code + message ----------
    const { errorCode, message: serverMessage } = parseErrorResponse(error.response.data)
    const status = error.response.status
    const isLoginRequest = originalRequest.url.includes('/auth/login') || originalRequest.url.includes('/auth/token')
    const isRefreshRequest = originalRequest.url.includes('/auth/refresh')

    // ---------- 401 处理：基于 error_code 区分 ----------
    if (status === 401) {
      // 登录请求 401 → 用户名密码错误，直接展示后端消息
      if (isLoginRequest) {
        return Promise.reject(createApiError(serverMessage || '用户名或密码错误', { errorCode }))
      }

      // 刷新请求 401 → Refresh Token 也过期了，需要重新登录
      if (isRefreshRequest) {
        authStore.logout()
        redirectToLogin()
        return Promise.reject(createApiError('登录已过期，请重新登录', { errorCode }))
      }

      // 已经重试过 → 不再重试
      if (originalRequest._retry) {
        authStore.logout()
        redirectToLogin()
        return Promise.reject(createApiError('登录已过期，请重新登录', { errorCode }))
      }

      // Token 过期（error_code === 'TOKEN_EXPIRED'）且有 refresh_token → 尝试刷新
      if (errorCode === 'TOKEN_EXPIRED' && authStore.refreshToken) {
        // 正在刷新中 → 加入等待队列
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh((newToken, err) => {
              if (err) {
                reject(err)
              } else if (newToken) {
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`
                originalRequest._retry = true
                resolve(api(originalRequest))
              } else {
                reject(createApiError('Token 刷新失败', { errorCode }))
              }
            })
          })
        }

        // 开始刷新 Token
        isRefreshing = true
        try {
          const refreshSuccess = await authStore.refreshAccessToken()
          isRefreshing = false

          if (refreshSuccess) {
            onTokenRefreshed(authStore.token)
            originalRequest.headers['Authorization'] = `Bearer ${authStore.token}`
            originalRequest._retry = true
            return api(originalRequest)
          }
        } catch (refreshError) {
          isRefreshing = false
          onRefreshFailed(refreshError)
        }
      }

      // 刷新失败或非过期的 401 → 跳转登录
      authStore.logout()
      redirectToLogin()
      return Promise.reject(createApiError('登录已过期，请重新登录', { errorCode }))
    }

    // ---------- 其他状态码：统一处理 ----------
    const fallbackMessages = {
      403: '没有权限访问该资源',
      404: '请求的资源不存在',
      405: '不允许的请求方法',
      500: '服务器内部错误，请联系管理员',
    }
    const errorMessage = serverMessage || fallbackMessages[status] || `请求失败：${status}`

    return Promise.reject(createApiError(errorMessage, { errorCode }))
  }
)

// 导出API实例
export { api }

// 导出API请求函数
export const authApi = {
  login: (data) => api.post('/v1/auth/login', data),
  getCurrentUser: () => api.get('/v1/users/me'),
  refreshToken: (data) => api.post('/v1/auth/refresh', data)
}

export const applicationApi = {
  list: (params) => api.get('/v1/applications/list', { params }),
  get: (appId) => api.get('/v1/applications/get', { params: { app_id: appId } }),
  create: (data) => api.post('/v1/applications/create', data),
  update: (appId, data) => api.post('/v1/applications/update', data, { params: { app_id: appId } }),
  delete: (appId) => api.post('/v1/applications/delete', null, { params: { app_id: appId } }),
  enable: (appId) => api.post('/v1/applications/enable', null, { params: { app_id: appId } }),
  disable: (appId) => api.post('/v1/applications/disable', null, { params: { app_id: appId } }),
  resetSecret: (appId) => api.post('/v1/applications/reset-secret', null, { params: { app_id: appId } }),
}

export const userApi = {
  list: (params) => api.get('/v1/users/list', { params }),
  get: (userId) => api.get('/v1/users/get', { params: { user_id: userId } }),
  create: (data) => api.post('/v1/users/create', data),
  update: (userId, data) => api.post('/v1/users/update', data, { params: { user_id: userId } }),
  enable: (userId) => api.post('/v1/users/enable', null, { params: { user_id: userId } }),
  disable: (userId) => api.post('/v1/users/disable', null, { params: { user_id: userId } }),
  resetPassword: (userId) => api.post('/v1/users/force-reset-password', null, { params: { user_id: userId } }),
  updatePassword: (data) => api.post('/v1/users/change-password', data),
}

export const roleApi = {
  list: () => api.get('/v1/roles/list'),
  get: (code) => api.get('/v1/roles/get', { params: { code } }),
  create: (data) => api.post('/v1/roles/create', data),
  update: (code, data) => api.post('/v1/roles/update', data, { params: { code } }),
  delete: (code) => api.post('/v1/roles/delete', null, { params: { code } }),
  // 角色下的用户
  users: (code) => api.get('/v1/roles/users', { params: { code } }),
  // 用户角色管理
  assignRole: (data) => api.post('/v1/users/assign-role', data),
  unassignRole: (data) => api.post('/v1/users/unassign-role', data),
  getUserRoles: (userId) => api.get('/v1/users/roles', { params: { user_id: userId } }),
}

// 组织 API
export const organizationApi = {
  list: () => api.get('/v1/org/list'),
  get: (orgId) => api.get('/v1/org/get', { params: { org_id: orgId } }),
  create: (data) => api.post('/v1/org/create', data),
  update: (orgId, data) => api.post('/v1/org/update', data, { params: { org_id: orgId } }),
  delete: (orgId, force = false) => api.post('/v1/org/delete', null, { params: { org_id: orgId, force } }),
}

// 部门 API
export const departmentApi = {
  list: (orgId) => api.get('/v1/org/dept/list', { params: { org_id: orgId } }),
  tree: (orgId) => api.get('/v1/org/dept/tree', { params: { org_id: orgId, include: 'employee_count' } }),
  get: (deptId) => api.get('/v1/org/dept/get', { params: { dept_id: deptId } }),
  create: (data) => api.post('/v1/org/dept/create', data),
  update: (deptId, data) => api.post('/v1/org/dept/update', data, { params: { dept_id: deptId } }),
  move: (deptId, newParentId) => api.post('/v1/org/dept/move', null, { params: { dept_id: deptId, new_parent_id: newParentId } }),
  delete: (deptId, force = false) => api.post('/v1/org/dept/delete', null, { params: { dept_id: deptId, force } }),
  getEmployees: (deptId, params = {}) => api.get('/v1/org/dept/employees', { params: { dept_id: deptId, ...params } }),
  addLeader: (data) => api.post('/v1/org/dept/add-leader', data),
  removeLeader: (deptId, employeeId) => api.post('/v1/org/dept/remove-leader', null, { params: { dept_id: deptId, employee_id: employeeId } }),
}

// 员工 API
export const employeeApi = {
  list: (params) => api.get('/v1/org/employee/list', { params }),
  get: (employeeId) => api.get('/v1/org/employee/get', { params: { employee_id: employeeId } }),
  create: (data) => api.post('/v1/org/employee/create', data),
  update: (employeeId, data) => api.post('/v1/org/employee/update', data, { params: { employee_id: employeeId } }),
  delete: (employeeId) => api.post('/v1/org/employee/delete', null, { params: { employee_id: employeeId } }),
  addToOrg: (data) => api.post('/v1/org/employee/add-to-org', data),
  removeFromOrg: (employeeId, orgId) => api.post('/v1/org/employee/remove-from-org', null, { params: { employee_id: employeeId, org_id: orgId } }),
  setPrimaryOrg: (employeeId, orgId) => api.post('/v1/org/employee/set-primary-org', null, { params: { employee_id: employeeId, org_id: orgId } }),
  addToDept: (data) => api.post('/v1/org/employee/add-to-dept', data),
  removeFromDept: (employeeId, deptId) => api.post('/v1/org/employee/remove-from-dept', null, { params: { employee_id: employeeId, dept_id: deptId } }),
  setPrimaryDept: (employeeId, deptId) => api.post('/v1/org/employee/set-primary-dept', null, { params: { employee_id: employeeId, dept_id: deptId } }),
  createAccount: (data) => api.post('/v1/org/employee/create-account', data),
  updateOrgStatus: (employeeId, orgId, status) => api.post('/v1/org/employee/update-org-status', null, { params: { employee_id: employeeId, org_id: orgId, status } }),
  updateAccountStatus: (employeeId, accountStatus) => api.post('/v1/org/employee/update-account-status', null, { params: { employee_id: employeeId, account_status: accountStatus } }),
}

// 企业微信同步 API
export const wechatWorkApi = {
  // 配置管理
  getConfig: (orgId) => api.get('/v1/wechat-work/config/get', { params: { org_id: orgId } }),
  bind: (data) => api.post('/v1/wechat-work/config/bind', data),
  unbind: (data) => api.post('/v1/wechat-work/config/unbind', data),
  // 同步操作
  initSync: (data) => api.post('/v1/wechat-work/sync/init', data),
  manualSync: (data) => api.post('/v1/wechat-work/sync/manual', data),
  syncStatus: (orgId) => api.get('/v1/wechat-work/sync/status', { params: { org_id: orgId } }),
  // 扫码登录
  getLoginConfig: () => api.get('/v1/auth/wechat-work/login-config'),
  login: (data) => api.post('/v1/auth/wechat-work/login', data),
  getOAuthUrl: (redirectUri, state = '') => api.get('/v1/auth/wechat-work/oauth-url', { params: { redirect_uri: redirectUri, state } }),
}

// SSO 角色 API
export const ssoRoleApi = {
  list: (activeOnly = false) => api.get('/v1/sso-roles/list', { params: { active_only: activeOnly } }),
  get: (code) => api.get('/v1/sso-roles/get', { params: { code } }),
  create: (data) => api.post('/v1/sso-roles/create', data),
  update: (code, data) => api.post('/v1/sso-roles/update', data, { params: { code } }),
  delete: (code) => api.post('/v1/sso-roles/delete', null, { params: { code } }),
  // 用户 SSO 角色管理
  getUserRoles: (userId) => api.get('/v1/sso-roles/user-roles', { params: { user_id: userId } }),
  assign: (data) => api.post('/v1/sso-roles/assign', data),
  unassign: (data) => api.post('/v1/sso-roles/unassign', data),
  setUserRoles: (data) => api.post('/v1/sso-roles/set-user-roles', data),
}

// 配置API
export const configApi = {
  list: () => api.get('/v1/configs'),
  getByKey: (key) => api.get(`/v1/configs/${key}`),
  update: (key, data) => api.put(`/v1/configs/${key}`, data),
  getJwt: () => api.get('/v1/configs/jwt'),
  updateJwt: (data) => api.put('/v1/configs/jwt', data),
  getWechat: () => api.get('/v1/configs/wechat'),
  updateWechat: (data) => api.put('/v1/configs/wechat', data)
}

// 缓存管理 API
export const cacheApi = {
  listFunctions: () => api.get('/v1/cache/functions'),
  getStats: (functionName) =>
    api.get('/v1/cache/stats', {
      params: { function_name: functionName || undefined }
    }),
  clear: (functionName) =>
    api.post('/v1/cache/clear', null, {
      params: { function_name: functionName || undefined }
    }),
  getInvalidatorRegistrations: () => api.get('/v1/cache/invalidator/registrations'),
  listEntries: (functionName, limit = 50) =>
    api.get('/v1/cache/entries', {
      params: { function_name: functionName, limit }
    }),
  getEntry: (functionName, key) =>
    api.get('/v1/cache/entry', {
      params: { function_name: functionName, key }
    }),
  toggleInvalidator: (enabled) =>
    api.post('/v1/cache/invalidator/toggle', null, {
      params: { enabled }
    }),
}

// OAuth2 API（SSO 授权服务器）
export const oauth2Api = {
  // 用户授权确认（需 JWT）
  authorize: (data) => api.post('/v1/oauth2/authorize', data),
}

// 权限 API
export const permissionApi = {
  // 获取权限树（按模块分组）
  tree: () => api.get('/v1/permissions/tree'),
  // 自动扫描路由同步权限
  scan: () => api.post('/v1/permissions/scan'),
  // 获取角色已分配的权限
  getRolePermissions: (code) => api.get('/v1/roles/permissions', { params: { code } }),
  // 全量设置角色权限
  setRolePermissions: (code, permissionIds) =>
    api.post('/v1/roles/set-permissions', { permission_ids: permissionIds }, { params: { code } }),
}

// 仪表盘API
export const dashboardApi = {
  getStatistics: () => api.get('/v1/dashboard/statistics'),
  getRecentLogins: (params) => api.get('/v1/login-records/list', { params }),
}