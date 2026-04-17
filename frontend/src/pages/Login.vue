<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>{{ siteStore.systemName }}</h1>
        <p>{{ siteStore.systemDesc }}</p>
      </div>

      <el-form
        :model="loginForm"
        :rules="loginRules"
        ref="loginFormRef"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            @keyup.enter="focusPassword"
          >
            <template #prefix>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            show-password
            size="large"
            ref="passwordInputRef"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <div class="login-actions">
          <el-checkbox v-model="loginForm.remember">记住密码</el-checkbox>
          <el-link type="primary" href="#" :underline="'never'"
            >忘记密码？</el-link
          >
        </div>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleLogin"
            size="large"
            block
          >
            登录
          </el-button>
        </el-form-item>

        <div class="login-footer" v-if="wechatLoginEnabled">
          <el-divider>其他登录方式</el-divider>
          <div class="other-login">
            <el-button
              @click="showWechatQrCode"
              :loading="wechatLoading"
              aria-label="使用企业微信登录"
            >
              <svg
                viewBox="0 0 1024 1024"
                width="18"
                height="18"
                style="margin-right: 6px; vertical-align: middle"
                aria-hidden="true"
              >
                <path
                  d="M688.6 323.2c-15.6-2-31.6-3.2-47.8-3.2-141.4 0-262.2 88.4-310.4 213-10.4-0.8-20.8-1.4-31.4-1.4C142.6 531.6 16 641.4 16 776.6c0 75.4 37.2 142.6 95.4 188.4l-23.8 71.6 83.2-41.6c30.6 10 62.8 15.6 96.2 15.6 15.8 0 31.2-1.2 46.4-3.4 48.2 124.4 169 213 310.4 213 26.2 0 51.6-3.4 75.8-9.6l104.2 52-29.8-89.6C844.6 1129 896 1054.2 896 966.6c0-64.8-30.4-123-78-165"
                  fill="#07C160"
                />
              </svg>
              企业微信登录
            </el-button>
          </div>
        </div>
      </el-form>
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
        style="margin-bottom: 20px"
      />
      <el-form
        :model="changePwdForm"
        :rules="changePwdRules"
        ref="changePwdFormRef"
        label-width="80px"
      >
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="changePwdForm.newPassword"
            type="password"
            placeholder="至少6位字符"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="changePwdForm.confirmPassword"
            type="password"
            placeholder="再次输入新密码"
            show-password
            @keyup.enter="handleChangePassword"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button
          type="primary"
          :loading="changePwdLoading"
          @click="handleChangePassword"
        >
          保存新密码
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>


<script setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { User, Lock } from "@element-plus/icons-vue";
import { wechatWorkApi } from "@/api";
import { useAuthStore } from "@/stores/auth";
import { useSiteStore } from "@/stores/site";
import { handleApiError } from "@/utils/errorHandler";

const siteStore = useSiteStore();

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const loginFormRef = ref(null);
const passwordInputRef = ref(null);
const loading = ref(false);

// 企业微信登录
const wechatLoginEnabled = ref(false);
const wechatLoginConfig = ref({});
const wechatLoading = ref(false);

// 登录表单
const loginForm = reactive({
  username: "",
  password: "",
  remember: false,
});

// 表单规则
const loginRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

// 强制修改密码
const changePasswordVisible = ref(false);
const changePwdLoading = ref(false);
const changePwdFormRef = ref(null);
const changePwdForm = reactive({
  newPassword: "",
  confirmPassword: "",
});
// 保存登录时的原始密码，用于 change-password 接口的 old_password
let loginPassword = "";

const changePwdRules = {
  newPassword: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "密码长度不能少于6位", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请再次输入新密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== changePwdForm.newPassword) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

// 聚焦到密码输入框
const focusPassword = async () => {
  await nextTick();
  if (passwordInputRef.value && passwordInputRef.value.focus) {
    passwordInputRef.value.focus();
  }
};

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) {
    return;
  }

  try {
    await loginFormRef.value.validate();
    loading.value = true;

    // 直接发送明文密码（后端使用 pbkdf2_sha256 验证，HTTPS 保证传输安全）
    const result = await authStore.login(
      loginForm.username,
      loginForm.password,
    );

    if (result.success) {
      if (result.mustChangePassword) {
        // 首次登录需要修改密码，保存原始密码用于验证
        loginPassword = loginForm.password;
        changePasswordVisible.value = true;
        ElMessage.warning("首次登录，请先修改默认密码");
      } else {
        ElMessage.success("登录成功");
        router.push("/sso/login");
      }
    } else {
      // 使用错误处理工具处理登录错误
      const error = new Error(result.error || "登录失败");
      error.isNetworkError = result.isNetworkError;
      error.isTimeoutError = result.isTimeoutError;

      // 根据错误类型显示不同的错误信息
      if (result.isTimeoutError) {
        handleApiError(error, "登录超时，请检查网络连接后重试");
      } else if (result.isNetworkError) {
        handleApiError(error, "网络连接失败，请检查网络设置或联系管理员");
      } else if (
        result.error &&
        (result.error.includes("用户名") || result.error.includes("密码"))
      ) {
        handleApiError(error, "用户名或密码错误，请重新输入");
      } else {
        handleApiError(error, "登录失败，请稍后重试");
      }
    }
  } catch (error) {
    handleApiError(error, "登录过程中发生异常，请稍后重试");
  } finally {
    loading.value = false;
  }
};

// 处理修改密码
const handleChangePassword = async () => {
  if (!changePwdFormRef.value) return;
  try {
    await changePwdFormRef.value.validate();
    changePwdLoading.value = true;
    const result = await authStore.changePassword(
      loginPassword,
      changePwdForm.newPassword,
    );
    if (result.success) {
      ElMessage.success("密码修改成功");
      changePasswordVisible.value = false;
      loginPassword = "";
      router.push("/sso/login");
    } else {
      ElMessage.error(result.error || "密码修改失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error.message || "密码修改失败");
    }
  } finally {
    changePwdLoading.value = false;
  }
};

// ==================== 企业微信登录 ====================

// 检测是否在企业微信内部
const isInWechatWork = () => {
  return /wxwork/i.test(navigator.userAgent);
};

// 加载企微登录配置
const loadWechatLoginConfig = async () => {
  try {
    const res = await wechatWorkApi.getLoginConfig();
    if (res.data?.enabled) {
      wechatLoginEnabled.value = true;
      wechatLoginConfig.value = res.data;
    }
  } catch {
    // 企微登录不可用，静默忽略
  }
};

// 显示企微扫码登录（跳转到企微授权页面）
const showWechatQrCode = async () => {
  if (!wechatLoginConfig.value.corp_id) {
    ElMessage.error("企业微信登录未配置");
    return;
  }
  wechatLoading.value = true;

  try {
    const config = wechatLoginConfig.value;
    const state = Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem("wechat_work_state", state);

    // 构造企微 Web 登录授权链接
    const redirectUri = encodeURIComponent(window.location.origin + "/login");
    const loginUrl =
      `https://login.work.weixin.qq.com/wwlogin/sso/login` +
      `?login_type=CorpApp` +
      `&appid=${config.corp_id}` +
      `&agentid=${config.agent_id}` +
      `&redirect_uri=${redirectUri}` +
      `&state=${state}`;

    window.location.href = loginUrl;
  } catch (e) {
    ElMessage.error("跳转企业微信登录失败");
  } finally {
    wechatLoading.value = false;
  }
};

// 处理企微扫码回调（URL 中携带 auth_code）
const handleWechatCallback = async () => {
  const authCode = route.query.auth_code || route.query.code;
  if (!authCode) return false;

  // 验证 state（CSRF 防护）
  const savedState = sessionStorage.getItem("wechat_work_state");
  const returnedState = route.query.state;
  if (savedState && returnedState && savedState !== returnedState) {
    ElMessage.error("安全验证失败，请重新扫码");
    return false;
  }
  sessionStorage.removeItem("wechat_work_state");

  loading.value = true;
  try {
    const res = await wechatWorkApi.login({ code: authCode });
    if (res.data?.access_token) {
      // 保存 token 到 authStore
      authStore.setTokens(res.data.access_token, res.data.refresh_token);
      authStore.setUserInfo(res.data.user);
      ElMessage.success("企业微信登录成功");
      router.push("/sso/login");
      return true;
    } else {
      ElMessage.error(res.message || "企业微信登录失败");
      return false;
    }
  } catch (e) {
    ElMessage.error(e.message || "企业微信登录失败");
    return false;
  } finally {
    loading.value = false;
    // 清理 URL 中的回调参数
    if (route.query.auth_code || route.query.code) {
      router.replace({ path: "/login", query: {} });
    }
  }
};

// 企微内部自动免登
const autoLoginInWechatWork = async () => {
  if (!isInWechatWork() || !wechatLoginEnabled.value) return;

  try {
    const redirectUri = window.location.origin + "/login";
    const state = Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem("wechat_work_state", state);

    const res = await wechatWorkApi.getOAuthUrl(redirectUri, state);
    if (res.data?.oauth_url) {
      setTimeout(() => {
        window.location.href = res.data.oauth_url;
      }, 200);
    }
  } catch {
    // 静默失败，用户可以手动登录
  }
};

// 页面加载时的初始化
onMounted(async () => {
  // 1. 检查 URL 是否携带企微回调的 auth_code
  const handled = await handleWechatCallback();
  if (handled) return;

  // 2. 加载企微登录配置
  await loadWechatLoginConfig();

  // 3. 如果在企微内部，自动触发免登
  if (isInWechatWork()) {
    autoLoginInWechatWork();
  }
});
</script>

<style scoped>


.login-form {
  margin-bottom: var(--spacing-medium);
}
/* 登录表单相关组件样式 */
.login-form .el-form-item {
  margin-bottom: var(--spacing-medium);
}

/* 登录表单输入框样式 - 通过输入框类控制 */
.login-form .el-input {
  border-radius: var(--bs-border-radius);
  transition: var(--app-transition);
}

.login-form .el-checkbox__label {
  color: var(--font-color);
  font-size: var(--p-font-size);
}

.login-form .el-link {
  font-size: var(--p-font-size);
  color: var(--el-color-primary);
}

.login-form .el-button--primary {
  height: 44px;
  border-radius: var(--bs-border-radius);
  font-size: var(--btn-font-size);
  font-weight: 500;
  letter-spacing: normal;
  box-shadow: none;
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  transition: var(--app-transition);
  width: 100%;
}

.login-form .el-button--primary:hover {
  background-color: var(--el-color-primary-light-3);
  border-color: var(--el-color-primary-light-3);
  box-shadow: var(--hover-shadow);
}

.login-form .el-button--primary:active {
  box-shadow: none;
}

.login-form .el-button--default {
  border-radius: var(--bs-border-radius);
  box-shadow: none;
  border: 1px solid var(--border_color);
  color: var(--font-color);
  transition: var(--app-transition);
}

.login-form .el-button--default:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
  box-shadow: var(--hover-shadow);
}

</style>
