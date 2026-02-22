import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')

  const mustChangePassword = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const roles = computed(() => userInfo.value?.roles || [])
  const isAdmin = computed(() => roles.value.includes('admin'))

  // 方法
  const login = async (username, password) => {
    try {
      console.log('开始执行登录请求，用户名:', username)
      const requestData = { username, password };
      console.log('发送登录请求数据:', requestData)
      
      const response = await api.post('/v1/auth/login', requestData)
      console.log('收到登录响应:', response)
      
      // BaseResponse 格式: { status, message, msg_details, data }
      const { access_token, refresh_token, token_type, user } = response.data
      console.log('解析响应数据，access_token:', access_token, 'user:', user)
      
      // 保存 Token
      token.value = access_token
      refreshToken.value = refresh_token
      userInfo.value = user
      mustChangePassword.value = !!user.must_change_password
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('refreshToken', refresh_token)
      localStorage.setItem('userInfo', JSON.stringify(user))
      console.log('登录信息保存完成')
      
      return { success: true, mustChangePassword: mustChangePassword.value }
    } catch (error) {
      console.error('登录失败:', error)
      return { 
        success: false, 
        error: error.message || '登录失败',
        isNetworkError: error.isNetworkError || false,
        isTimeoutError: error.isTimeoutError || false
      }
    }
  }

  const changePassword = async (oldPassword, newPassword) => {
    try {
      await api.post('/v1/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      mustChangePassword.value = false
      if (userInfo.value) {
        userInfo.value.must_change_password = false
        localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
      }
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message || '修改密码失败' }
    }
  }

  const logout = () => {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    mustChangePassword.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('userInfo')
  }

  /**
   * 使用 Refresh Token 刷新 Access Token
   * 如果 Refresh Token 即将过期，后端会返回新的 Refresh Token
   * 
   * @returns {Promise<boolean>} 刷新是否成功
   */
  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      return false
    }
    
    try {
      // 发送 refresh_token 到 body（与后端 RefreshRequest 对应）
      const response = await api.post('/v1/auth/refresh', {
        refresh_token: refreshToken.value
      })
      
      const { access_token, refresh_token: newRefreshToken } = response.data
      
      if (!access_token) {
        return false
      }
      
      // 更新 Access Token
      token.value = access_token
      localStorage.setItem('token', access_token)
      
      // 如果返回了新的 Refresh Token（滑动过期续期），也更新它
      if (newRefreshToken) {
        refreshToken.value = newRefreshToken
        localStorage.setItem('refreshToken', newRefreshToken)
      }
      
      return true
    } catch (error) {
      // 刷新失败，清除登录状态
      logout()
      return false
    }
  }

  /**
   * 更新 Access Token（简单更新，不涉及 Refresh Token）
   */
  const updateToken = (newToken) => {
    if (newToken) {
      token.value = newToken
      localStorage.setItem('token', newToken)
      console.log('Token 已更新')
    }
  }

  const getCurrentUser = async () => {
    if (!token.value) return null
    
    try {
      const response = await api.get('/v1/users/me')
      userInfo.value = response.data
      localStorage.setItem('userInfo', JSON.stringify(response.data))
      return userInfo.value
    } catch (error) {
      console.error('获取用户信息失败:', error)
      logout()
      return null
    }
  }

  // 从本地存储恢复认证状态
  const restoreAuthState = () => {
    const savedToken = localStorage.getItem('token')
    const savedRefreshToken = localStorage.getItem('refreshToken')
    const savedUserInfo = localStorage.getItem('userInfo')
    
    if (savedToken && savedUserInfo) {
      try {
        token.value = savedToken
        refreshToken.value = savedRefreshToken || ''
        const parsedUser = JSON.parse(savedUserInfo)
        userInfo.value = parsedUser
        mustChangePassword.value = !!parsedUser.must_change_password
        console.log('认证状态已从本地存储恢复')
        return true
      } catch (error) {
        console.error('恢复认证状态失败:', error)
        logout()
        return false
      }
    }
    return false
  }

  /**
   * 直接设置 Token（用于第三方登录等非标准登录流程）
   */
  const setTokens = (accessToken, newRefreshToken) => {
    token.value = accessToken
    refreshToken.value = newRefreshToken || ''
    localStorage.setItem('token', accessToken)
    if (newRefreshToken) {
      localStorage.setItem('refreshToken', newRefreshToken)
    }
  }

  /**
   * 直接设置用户信息（用于第三方登录等非标准登录流程）
   */
  const setUserInfo = (user) => {
    userInfo.value = user
    mustChangePassword.value = !!user?.must_change_password
    if (user) {
      localStorage.setItem('userInfo', JSON.stringify(user))
    }
  }

  return {
    userInfo,
    token,
    refreshToken,
    mustChangePassword,
    isLoggedIn,
    roles,
    isAdmin,
    login,
    logout,
    changePassword,
    updateToken,
    setTokens,
    setUserInfo,
    refreshAccessToken,
    getCurrentUser,
    restoreAuthState
  }
})
