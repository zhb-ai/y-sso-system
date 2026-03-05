import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { wechatWorkApi } from '../api'
import { useAuthStore } from '../stores/auth'

/**
 * 企业微信登录 Composable
 * @param {Object} options - 配置选项
 * @param {string} options.redirectPath - 登录成功后的跳转路径（用于构造回调URL）
 * @param {Function} options.onLoginSuccess - 登录成功后的回调函数
 * @returns {Object} 企业微信登录相关方法和状态
 */
export function useWechatWorkLogin(options = {}) {
  const { redirectPath = '/login', onLoginSuccess } = options

  const route = useRoute()
  const router = useRouter()
  const authStore = useAuthStore()

  // 状态
  const wechatLoginEnabled = ref(false)
  const wechatLoginConfig = ref({})
  const wechatLoading = ref(false)

  /**
   * 检测是否在企业微信内部
   */
  const isInWechatWork = () => {
    return /wxwork/i.test(navigator.userAgent)
  }

  /**
   * 加载企微登录配置
   */
  const loadWechatLoginConfig = async () => {
    try {
      const res = await wechatWorkApi.getLoginConfig()
      if (res.data?.enabled) {
        wechatLoginEnabled.value = true
        wechatLoginConfig.value = res.data
      }
    } catch {
      // 企微登录不可用，静默忽略
    }
  }

  /**
   * 显示企微扫码登录（跳转到企微授权页面）
   */
  const showWechatQrCode = async () => {
    if (!wechatLoginConfig.value.corp_id) {
      ElMessage.error('企业微信登录未配置')
      return
    }
    wechatLoading.value = true

    try {
      const config = wechatLoginConfig.value
      const state = Math.random().toString(36).substring(2, 15)
      sessionStorage.setItem('wechat_work_state', state)

      // 保存当前完整 URL（包含 OAuth2 参数），登录成功后用于刷新页面
      sessionStorage.setItem('wechat_work_original_url', window.location.href)

      // 构造企微 Web 登录授权链接
      const redirectUri = encodeURIComponent(window.location.origin + redirectPath)
      const loginUrl =
        `https://login.work.weixin.qq.com/wwlogin/sso/login` +
        `?login_type=CorpApp` +
        `&appid=${config.corp_id}` +
        `&agentid=${config.agent_id}` +
        `&redirect_uri=${redirectUri}` +
        `&state=${state}`

      window.location.href = loginUrl
    } catch (e) {
      ElMessage.error('跳转企业微信登录失败')
    } finally {
      wechatLoading.value = false
    }
  }

  /**
   * 处理企微扫码回调（URL 中携带 auth_code）
   * @returns {Promise<boolean>} 是否成功处理了回调
   */
  const handleWechatCallback = async () => {
    const authCode = route.query.auth_code || route.query.code
    if (!authCode) return false

    // 验证 state（CSRF 防护）
    const savedState = sessionStorage.getItem('wechat_work_state')
    const returnedState = route.query.state
    if (savedState && returnedState && savedState !== returnedState) {
      ElMessage.error('安全验证失败，请重新扫码')
      return false
    }
    sessionStorage.removeItem('wechat_work_state')

    wechatLoading.value = true
    try {
      const res = await wechatWorkApi.login({ code: authCode })
      if (res.data?.access_token) {
        // 保存 token 到 authStore
        authStore.setTokens(res.data.access_token, res.data.refresh_token)
        authStore.setUserInfo(res.data.user)
        ElMessage.success('企业微信登录成功')

        // 执行登录成功回调
        if (onLoginSuccess) {
          await onLoginSuccess()
        }

        return true
      } else {
        ElMessage.error(res.message || '企业微信登录失败')
        return false
      }
    } catch (e) {
      ElMessage.error(e.message || '企业微信登录失败')
      return false
    } finally {
      wechatLoading.value = false
      // 清理 URL 中的回调参数
      if (route.query.auth_code || route.query.code) {
        // 获取保存的原始 URL，用原始 URL 刷新页面以保留 OAuth2 参数
        const originalUrl = sessionStorage.getItem('wechat_work_original_url')
        sessionStorage.removeItem('wechat_work_original_url')
        if (originalUrl) {
          window.location.replace(originalUrl)
        } else {
          router.replace({ path: redirectPath, query: {} })
        }
      }
    }
  }

  /**
   * 企微内部自动免登
   */
  const autoLoginInWechatWork = async () => {
    if (!isInWechatWork() || !wechatLoginEnabled.value) return

    try {
      // 保存当前完整 URL（包含 OAuth2 参数），登录成功后用于刷新页面
      sessionStorage.setItem('wechat_work_original_url', window.location.href)

      const redirectUri = window.location.origin + redirectPath
      const state = Math.random().toString(36).substring(2, 15)
      sessionStorage.setItem('wechat_work_state', state)

      const res = await wechatWorkApi.getOAuthUrl(redirectUri, state)
      if (res.data?.oauth_url) {
        window.location.href = res.data.oauth_url
      }
    } catch {
      // 静默失败，用户可以手动登录
    }
  }

  /**
   * 初始化企业微信登录
   * 在组件 onMounted 中调用
   */
  const initWechatWorkLogin = async () => {
    // 1. 检查 URL 是否携带企微回调的 auth_code
    const handled = await handleWechatCallback()
    if (handled) return true

    // 2. 加载企微登录配置
    await loadWechatLoginConfig()

    // 3. 如果在企微内部，自动触发免登
    if (isInWechatWork()) {
      autoLoginInWechatWork()
    }

    return false
  }

  return {
    // 状态
    wechatLoginEnabled,
    wechatLoginConfig,
    wechatLoading,
    // 方法
    isInWechatWork,
    loadWechatLoginConfig,
    showWechatQrCode,
    handleWechatCallback,
    autoLoginInWechatWork,
    initWechatWorkLogin,
  }
}
