<template>
  <div class="login-container">
    <div class="login-box sso-login-box" :class="`columns-${!isOAuth2Mode && isLoggedIn ? Math.min(Math.ceil(availableApps.length / 3), 4) : 1}`">
      <!-- SSO 头部 -->
      <div class="login-header">
        <h1>{{ siteStore.systemName }}</h1>
        <p v-if="isOAuth2Mode && appName">{{ appName }} 请求访问您的账户</p>
        <p v-else>{{ siteStore.systemDesc }}</p>
      </div>

      <!-- ==================== OAuth2 模式：外部应用发起的授权 ==================== -->
      <template v-if="isOAuth2Mode">

        <!-- 已登录：显示授权确认 -->
        <div v-if="isLoggedIn" class="sso-authorize-section">
          <div class="sso-user-info">
            <el-icon :size="48" class="sso-user-avatar"><UserFilled /></el-icon>
            <div class="sso-user-detail">
              <span class="sso-username">{{ authStore.userInfo?.username }}</span>
              <span class="sso-email">{{ authStore.userInfo?.email || '' }}</span>
            </div>
          </div>

          <el-divider />

          <div class="sso-scope-info">
            <p class="sso-scope-title">此应用将获得以下权限：</p>
            <ul class="sso-scope-list">
              <li>访问您的基本资料（用户名、邮箱）</li>
              <li>读取您的角色信息</li>
            </ul>
          </div>

          <div class="sso-actions">
            <el-button type="primary" size="large" :loading="authorizing" @click="handleAuthorize" class="btn-full">
              授权并继续
            </el-button>
            <el-button size="large" @click="handleCancel" class="btn-full btn-secondary">
              取消
            </el-button>
          </div>
        </div>

        <!-- 未登录：显示登录表单 -->
        <template v-else>
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" class="login-form">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large" @keyup.enter="focusPassword">
                <template #prefix><el-icon><UserFilled /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password size="large"
                ref="passwordInputRef" @keyup.enter="handleLogin">
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleLogin" size="large" class="btn-full">
                登录并授权
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 企业微信登录 -->
          <div class="login-footer" v-if="wechatLoginEnabled">
            <el-divider>其他登录方式</el-divider>
            <div class="other-login">
              <el-button @click="showWechatQrCode" :loading="wechatLoading" size="large" class="btn-full">
                <svg viewBox="0 0 1024 1024" width="18" height="18" class="wechat-icon">
                  <path d="M688.6 323.2c-15.6-2-31.6-3.2-47.8-3.2-141.4 0-262.2 88.4-310.4 213-10.4-0.8-20.8-1.4-31.4-1.4C142.6 531.6 16 641.4 16 776.6c0 75.4 37.2 142.6 95.4 188.4l-23.8 71.6 83.2-41.6c30.6 10 62.8 15.6 96.2 15.6 15.8 0 31.2-1.2 46.4-3.4 48.2 124.4 169 213 310.4 213 26.2 0 51.6-3.4 75.8-9.6l104.2 52-29.8-89.6C844.6 1129 896 1054.2 896 966.6c0-64.8-30.4-123-78-165" fill="#07C160"/>
                </svg>
                企业微信登录
              </el-button>
            </div>
          </div>
        </template>
      </template>

      <!-- ==================== 门户模式：直接访问，展示应用列表 ==================== -->
      <template v-else>

        <!-- 已登录：显示应用列表 -->
        <div v-if="isLoggedIn" class="sso-portal-section">
          <div class="sso-user-info">
            <el-icon :size="48" class="sso-user-avatar"><UserFilled /></el-icon>
            <div class="sso-user-detail">
              <span class="sso-username">{{ authStore.userInfo?.username }}</span>
              <span class="sso-email">{{ authStore.userInfo?.email || '' }}</span>
            </div>
          </div>

          <el-divider />

          <p class="sso-portal-title">选择要登录的应用：</p>

          <!-- 加载中 -->
          <div v-if="loadingApps" class="sso-portal-loading">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
            <span>加载应用列表...</span>
          </div>

          <!-- 无可用应用 -->
          <el-empty v-else-if="availableApps.length === 0" description="暂无可用应用" :image-size="80" />

          <!-- 应用列表 -->
          <div v-else class="sso-app-list" :class="`columns-${Math.min(Math.ceil(availableApps.length / 3), 4)}`">
            <div
              v-for="app in availableApps"
              :key="app.id"
              class="sso-app-card"
              :class="{ 'is-jumping': jumpingAppId === app.id }"
              :style="app.logo_url ? { '--app-logo': `url(${app.logo_url})` } : {}"
              @click="handleAppClick(app)"
            >
              <div class="sso-app-content">
                <div class="sso-app-icon">
                  <el-icon :size="28" class="sso-app-icon-default"><Monitor /></el-icon>
                </div>
                <div class="sso-app-info">
                  <span class="sso-app-name">{{ app.name }}</span>
                  <span class="sso-app-desc">{{ app.description || app.code }}</span>
                </div>
              </div>
              <el-icon class="sso-app-arrow"><ArrowRight /></el-icon>
            </div>
          </div>

          <el-divider />
          <div class="sso-footer-links">
            <el-link v-if="authStore.isAdmin" type="primary" :underline="'never'" @click="$router.push('/dashboard')">
              进入管理后台
            </el-link>
            <el-link type="info" :underline="'never'" @click="handleLogout">
              退出登录
            </el-link>
          </div>
        </div>

        <!-- 未登录：显示登录表单 -->
        <template v-else>
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" class="login-form">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large" @keyup.enter="focusPassword">
                <template #prefix><el-icon><UserFilled /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password size="large"
                ref="passwordInputRef" @keyup.enter="handlePortalLogin">
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handlePortalLogin" size="large" class="btn-full">
                登录
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 企业微信登录 -->
          <div class="login-footer" v-if="wechatLoginEnabled">
            <el-divider>其他登录方式</el-divider>
            <div class="other-login">
              <el-button @click="showWechatQrCode" :loading="wechatLoading" size="large" class="btn-full">
                <svg viewBox="0 0 1024 1024" width="18" height="18" class="wechat-icon">
                  <path d="M688.6 323.2c-15.6-2-31.6-3.2-47.8-3.2-141.4 0-262.2 88.4-310.4 213-10.4-0.8-20.8-1.4-31.4-1.4C142.6 531.6 16 641.4 16 776.6c0 75.4 37.2 142.6 95.4 188.4l-23.8 71.6 83.2-41.6c30.6 10 62.8 15.6 96.2 15.6 15.8 0 31.2-1.2 46.4-3.4 48.2 124.4 169 213 310.4 213 26.2 0 51.6-3.4 75.8-9.6l104.2 52-29.8-89.6C844.6 1129 896 1054.2 896 966.6c0-64.8-30.4-123-78-165" fill="#07C160"/>
                </svg>
                企业微信登录
              </el-button>
            </div>
          </div>
        </template>
      </template>

    </div>

    <!-- 强制修改密码对话框 -->
    <el-dialog
      v-model="changePasswordVisible"
      title="首次登录 — 请修改密码"
      width="420px"
      align-center
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <el-alert
        title="您正在使用默认密码，为了账号安全请立即修改"
        type="warning"
        :closable="false"
        show-icon
        class="mb-4"
      />
      <el-form :model="changePwdForm" :rules="changePwdRules" ref="changePwdFormRef" label-width="80px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="changePwdForm.newPassword" type="password" placeholder="请输入新密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="changePwdForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password @keyup.enter="handleChangePassword" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="changePwdLoading" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled, Lock, Monitor, ArrowRight, Loading } from '@element-plus/icons-vue'
import { api, oauth2Api } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useSiteStore } from '@/stores/site'
import { handleApiError } from '@/utils/errorHandler'
import { useWechatWorkLogin } from '@/composables/useWechatWorkLogin'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const loginFormRef = ref(null)
const passwordInputRef = ref(null)
const loading = ref(false)
const authorizing = ref(false)

// 企业微信登录
const {
  wechatLoginEnabled,
  wechatLoading,
  showWechatQrCode,
  initWechatWorkLogin,
} = useWechatWorkLogin({
  redirectPath: '/sso/login',
  onLoginSuccess: async () => {
    // 如果是 OAuth2 模式，自动授权跳转
    if (isOAuth2Mode.value) {
      await doAuthorize()
    }
  },
})

// ==================== OAuth2 参数 ====================

const clientId = computed(() => route.query.client_id || '')
const redirectUri = computed(() => route.query.redirect_uri || '')
const responseType = computed(() => route.query.response_type || 'code')
const scope = computed(() => route.query.scope || '')
const state = computed(() => route.query.state || '')
const appName = computed(() => route.query.app_name || '')

// 两种模式判断：有 client_id → OAuth2 模式，否则 → 门户模式
const isOAuth2Mode = computed(() => !!clientId.value)
const isLoggedIn = computed(() => authStore.isLoggedIn)

// ==================== 门户模式：应用列表 ====================

const loadingApps = ref(false)
const availableApps = ref([])
const jumpingAppId = ref(null)

async function fetchAvailableApps() {
  try {
    loadingApps.value = true
    // 使用 SSO 门户专用端点（仅需认证，无需管理权限）
    const response = await api.get('/v1/sso/apps')
    availableApps.value = response.data || []
  } catch (error) {
    handleApiError(error, '获取应用列表失败')
  } finally {
    loadingApps.value = false
  }
}

// 已登录且在门户模式下，自动加载应用列表
watch(
  () => isLoggedIn.value && !isOAuth2Mode.value,
  (shouldLoad) => {
    if (shouldLoad) fetchAvailableApps()
  },
  { immediate: true }
)

// 点击应用卡片 → 授权并跳转
async function handleAppClick(app) {
  const uris = app.redirect_uris
  if (!uris || uris.length === 0) {
    ElMessage.warning('该应用未配置重定向地址')
    return
  }
  // url[1] 应用的登录地址
  if (uris.length > 1){
    window.open(uris[1], '_blank')
  } else {
    jumpingAppId.value = app.id
    try {
      const response = await oauth2Api.authorize({
        client_id: app.client_id,
        redirect_uri: uris[0],  // 使用第一个 redirect_uri
        scope: 'openid profile email',
        state: null,
      })
      const redirectUrl = response.data?.redirect_url || response.redirect_url
      if (redirectUrl) {
        window.open(redirectUrl, '_blank')
      } else {
        ElMessage.error('授权失败：未获取到重定向地址')
      }
    } catch (error) {
      handleApiError(error, '授权失败')
    } finally {
      jumpingAppId.value = null
    }
  }
}

// ==================== 登录表单 ====================

const loginForm = reactive({
  username: '',
  password: '',
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const focusPassword = async () => {
  await nextTick()
  passwordInputRef.value?.focus?.()
}

// ==================== 强制修改密码 ====================

const changePasswordVisible = ref(false)
const changePwdLoading = ref(false)
const changePwdFormRef = ref(null)
const changePwdForm = reactive({ newPassword: '', confirmPassword: '' })
let loginPassword = ''

const changePwdRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== changePwdForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleChangePassword() {
  if (!changePwdFormRef.value) return
  try {
    await changePwdFormRef.value.validate()
    changePwdLoading.value = true
    const result = await authStore.changePassword(loginPassword, changePwdForm.newPassword)
    if (result.success) {
      ElMessage.success('密码修改成功')
      changePasswordVisible.value = false
      loginPassword = ''
      // 密码修改后，watch 会自动检测 isLoggedIn 并加载应用列表
    } else {
      ElMessage.error(result.error || '密码修改失败')
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.message || '密码修改失败')
  } finally {
    changePwdLoading.value = false
  }
}

onMounted(async () => {
  authStore.restoreAuthState()

  // 初始化企业微信登录
  await initWechatWorkLogin()
})

// ==================== OAuth2 模式操作 ====================

async function doAuthorize() {
  try {
    authorizing.value = true
    const response = await oauth2Api.authorize({
      client_id: clientId.value,
      redirect_uri: redirectUri.value,
      scope: scope.value || null,
      state: state.value || null,
    })
    const redirectUrl = response.data?.redirect_url || response.redirect_url
    if (redirectUrl) {
      setTimeout(() => {
        window.location.href = redirectUrl
      }, 200);
    } else {
      ElMessage.error('授权失败：未获取到重定向地址')
    }
  } catch (error) {
    handleApiError(error, '授权失败')
  } finally {
    authorizing.value = false
  }
}

function handleAuthorize() {
  doAuthorize()
}

function handleCancel() {
  const params = new URLSearchParams({
    error: 'access_denied',
    error_description: 'User denied the request',
  })
  if (state.value) params.set('state', state.value)
  setTimeout(() => {
    window.location.href = `${redirectUri.value}?${params.toString()}`
  }, 200);
}

// OAuth2 模式登录：登录后自动授权
async function handleLogin() {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
    loading.value = true
    const result = await authStore.login(loginForm.username, loginForm.password)
    if (result.success) {
      if (result.mustChangePassword) {
        loginPassword = loginForm.password
        changePasswordVisible.value = true
        ElMessage.warning('首次登录，请先修改默认密码')
      } else {
        ElMessage.success('登录成功，正在授权...')
        await doAuthorize()
      }
    } else {
      const error = new Error(result.error || '登录失败')
      error.isNetworkError = result.isNetworkError
      error.isTimeoutError = result.isTimeoutError
      handleApiError(error, '登录失败')
    }
  } catch (error) {
    handleApiError(error, '登录过程中发生异常')
  } finally {
    loading.value = false
  }
}

// 退出登录
function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 门户模式登录：登录后加载应用列表（由 watch 自动触发）
async function handlePortalLogin() {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
    loading.value = true
    const result = await authStore.login(loginForm.username, loginForm.password)
    if (result.success) {
      if (result.mustChangePassword) {
        loginPassword = loginForm.password
        changePasswordVisible.value = true
        ElMessage.warning('首次登录，请先修改默认密码')
      } else {
        ElMessage.success('登录成功')
        // watch 会自动检测 isLoggedIn 变化并加载应用列表
      }
    } else {
      const error = new Error(result.error || '登录失败')
      error.isNetworkError = result.isNetworkError
      error.isTimeoutError = result.isTimeoutError
      handleApiError(error, '登录失败')
    }
  } catch (error) {
    handleApiError(error, '登录过程中发生异常')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>

.login-form {
  margin-bottom: var(--spacing-medium);
}
.sso-login-box {
  width: 100%;
  max-width: 400px;
  transition: max-width 0.3s ease;
}

/*
  宽度计算公式：列数量*280px + (列数量-1)*12px + 80px(左右padding各40px)
  1列: 280 + 0 + 80 = 360px → 400px (留一些余量)
  2列: 560 + 12 + 80 = 652px → 680px
  3列: 840 + 24 + 80 = 944px → 960px
  4列: 1120 + 36 + 80 = 1236px → 1240px
*/
.sso-login-box.columns-2 {
  max-width: 680px;
}

.sso-login-box.columns-3 {
  max-width: 960px;
}

.sso-login-box.columns-4 {
  max-width: 1240px;
}

/* 登录容器添加横向滚动支持 */
.login-container {
  overflow-x: auto;
  padding: 20px;
}

/* ==================== 用户信息 ==================== */

.sso-authorize-section,
.sso-portal-section {
  padding: 10px 0;
}

.sso-user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
}

.sso-user-avatar {
  color: var(--el-color-primary);
}

.sso-user-detail {
  display: flex;
  flex-direction: column;
}

.sso-username {
  font-size: var(--el-font-size-lg);
  font-weight: var(--el-font-weight-extra-bold);
  color: var(--el-text-color-primary);
}

.sso-email {
  font-size: var(--el-font-size-sm);
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

/* ==================== OAuth2 授权确认 ==================== */

.sso-scope-info {
  margin: 8px 0 20px;
}

.sso-scope-title {
  font-size: var(--el-font-size-base);
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.sso-scope-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sso-scope-list li {
  position: relative;
  padding-left: 20px;
  margin-bottom: 6px;
  font-size: var(--el-font-size-sm);
  color: var(--el-text-color-secondary);
}

.sso-scope-list li::before {
  content: '\2713';
  position: absolute;
  left: 0;
  color: var(--el-color-success);
  font-weight: bold;
}

.sso-actions {
  display: flex;
  flex-direction: column;
}

/* ==================== 门户模式：应用列表 ==================== */

.sso-portal-title {
  font-size: var(--el-font-size-base);
  color: var(--el-text-color-regular);
  margin-bottom: 12px;
}

.sso-portal-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 0;
  color: var(--el-text-color-secondary);
  font-size: var(--el-font-size-base);
}

.sso-app-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow-y: auto;
}

/* 多列布局 - 每列固定3个应用，纵向排列 */
.sso-app-list.columns-2,
.sso-app-list.columns-3,
.sso-app-list.columns-4 {
  display: grid;
  grid-auto-flow: column;
  grid-template-rows: repeat(3, 1fr);
  gap: 12px;
  max-height: none;
  overflow-y: visible;
  justify-content: space-between;
}

.sso-app-list.columns-2 {
  grid-template-columns: repeat(2, 280px);
}

.sso-app-list.columns-3 {
  grid-template-columns: repeat(3, 280px);
}

.sso-app-list.columns-4 {
  grid-template-columns: repeat(4, 280px);
}

.sso-app-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--el-bg-color);
  position: relative;
  overflow: hidden;
}

/* 有logo时添加背景图 */
.sso-app-card[style*="--app-logo"]::before {
  content: '';
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  width: 60px;
  height: 60px;
  background-image: var(--app-logo);
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.08;
  pointer-events: none;
  z-index: 0;
}

.sso-app-card:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.sso-app-card.is-jumping {
  opacity: 0.6;
  pointer-events: none;
}

.sso-app-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.sso-app-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.sso-app-icon-default {
  color: var(--el-color-primary);
}

.sso-app-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.sso-app-name {
  font-size: var(--el-font-size-sm);
  font-weight: var(--el-font-weight-bold);
  color: var(--el-text-color-primary);
}

.sso-app-desc {
  font-size: var(--el-font-size-xs);
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.sso-app-arrow {
  flex-shrink: 0;
  color: var(--el-text-color-placeholder);
  transition: color 0.2s;
  position: relative;
  z-index: 1;
}

.sso-app-card:hover .sso-app-arrow {
  color: var(--el-color-primary);
}

.sso-app-name,
.sso-app-desc {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ==================== 通用工具类 ==================== */

.btn-full {
  width: 100%;
}


.btn-secondary {
  color: var(--white);
  background-color: rgba(var(--secondary), 1);
  border-color: rgba(var(--secondary), 1);
  margin-top: 10px;
  margin-left: 0;
}

.btn-secondary:hover {
  background-color: rgba(var(--secondary), 0.9);
  border-color: rgba(var(--secondary), 0.9);
}

.wechat-icon {
  margin-right: 6px;
  vertical-align: middle;
}

.mb-4 {
  margin-bottom: 20px;
}

/* ==================== 底部链接区域 ==================== */

.sso-footer-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 24px;
}

/* ==================== 企业微信登录 ==================== */

.login-footer {
  margin-top: 20px;
}

.other-login {
  display: flex;
  justify-content: center;
}
</style>
