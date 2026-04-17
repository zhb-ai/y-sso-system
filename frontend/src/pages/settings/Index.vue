<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>
    
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 站点信息 -->
      <el-tab-pane label="站点信息" name="site">
        <el-card class="form-card">
          <div class="section-header">
            <div class="section-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="section-info">
              <h3 class="section-title">站点信息配置</h3>
              <p class="section-desc">配置系统的基本信息，包括名称、描述和 Logo</p>
            </div>
          </div>
          
          <el-form :model="siteSettings" ref="siteFormRef" label-position="top" class="compact-form">
            <div class="form-row">
              <el-form-item label="系统名称" prop="system_name" class="form-item-half">
                <el-input
                  v-model="siteSettings.system_name"
                  placeholder="请输入系统名称"
                  maxlength="100"
                  show-word-limit
                />
              </el-form-item>
              
              <el-form-item label="系统 Logo URL" prop="system_logo" class="form-item-half">
                <el-input
                  v-model="siteSettings.system_logo"
                  placeholder="请输入系统 Logo 图片地址"
                />
              </el-form-item>
            </div>
            
            <div v-if="siteSettings.system_logo" class="logo-preview">
              <span class="preview-label">Logo 预览</span>
              <el-image :src="siteSettings.system_logo" style="height: 48px" fit="contain">
                <template #error>
                  <span class="preview-error">图片加载失败</span>
                </template>
              </el-image>
            </div>

            <el-form-item label="系统描述" prop="system_desc">
              <el-input
                v-model="siteSettings.system_desc"
                type="textarea"
                :rows="2"
                placeholder="请输入系统描述"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item class="form-actions">
              <el-button type="primary" @click="handleSaveSite" :loading="saveLoading">
                <el-icon><Check /></el-icon> 保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- JWT 认证（只读） -->
      <el-tab-pane label="JWT 认证" name="jwt">
        <el-card class="form-card">
          <div class="section-header">
            <div class="section-icon jwt">
              <el-icon><Key /></el-icon>
            </div>
            <div class="section-info">
              <h3 class="section-title">JWT 认证配置</h3>
              <p class="section-desc">查看 JWT 认证相关配置，如需修改请编辑配置文件</p>
            </div>
          </div>
          
          <el-alert
            title="JWT 配置为只读"
            description="JWT 配置来自 config/settings.yaml，如需修改请直接编辑配置文件并重启服务。"
            type="info"
            :closable="false"
            show-icon
            class="jwt-alert"
          />
          
          <div class="jwt-config-grid">
            <div class="jwt-config-item">
              <span class="config-label">JWT 密钥</span>
              <el-tag type="info" class="config-value">{{ jwtSettings.secret_key || '未配置' }}</el-tag>
            </div>
            <div class="jwt-config-item">
              <span class="config-label">签名算法</span>
              <span class="config-value">{{ jwtSettings.algorithm }}</span>
            </div>
            <div class="jwt-config-item">
              <span class="config-label">Access Token 有效期</span>
              <span class="config-value">{{ jwtSettings.access_token_expire_minutes }} 分钟</span>
            </div>
            <div class="jwt-config-item">
              <span class="config-label">Refresh Token 有效期</span>
              <span class="config-value">{{ jwtSettings.refresh_token_expire_days }} 天</span>
            </div>
            <div class="jwt-config-item full-width">
              <span class="config-label">滑动续期阈值</span>
              <span class="config-value">{{ jwtSettings.refresh_token_sliding_days }} 天</span>
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Key, Check } from '@element-plus/icons-vue'
import { api } from '@/api'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()

const activeTab = ref('site')
const saveLoading = ref(false)

// ==================== 站点信息 ====================
const siteFormRef = ref(null)
const siteSettings = reactive({
  system_name: '单点登录系统',
  system_desc: '统一身份认证平台',
  system_logo: '',
})

const loadSiteSettings = async () => {
  try {
    const res = await api.get('/v1/settings/site')
    Object.assign(siteSettings, res.data || {})
  } catch {
    // 首次加载失败用默认值
  }
}

const handleSaveSite = async () => {
  saveLoading.value = true
  try {
    await api.post('/v1/settings/site', siteSettings)
    await siteStore.refresh()
    ElMessage.success('站点信息保存成功')
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saveLoading.value = false
  }
}

// ==================== JWT 配置（只读） ====================
const jwtSettings = reactive({
  secret_key: '',
  algorithm: 'HS256',
  access_token_expire_minutes: 30,
  refresh_token_expire_days: 7,
  refresh_token_sliding_days: 2,
})

const loadJwtSettings = async () => {
  try {
    const res = await api.get('/v1/settings/jwt')
    Object.assign(jwtSettings, res.data || {})
  } catch {
    // 加载失败用默认值
  }
}

// ==================== 初始化 ====================
onMounted(() => {
  loadSiteSettings()
  loadJwtSettings()
})
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}

.settings-tabs {
  margin-top: 20px;
}

.form-card {
  margin-bottom: 20px;
  padding: 8px;
}

/* 区块头部样式 */
.section-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.section-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.section-icon.jwt {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.section-info {
  flex: 1;
  padding-top: 4px;
}

.section-title {
  margin: 0 0 6px 0;
  font-size: var(--el-font-size-large);
  font-weight: var(--el-font-weight-bold);
  color: var(--el-text-color-primary);
}

.section-desc {
  margin: 0;
  font-size: var(--el-font-size-small);
  color: var(--el-text-color-secondary);
}

/* 紧凑表单样式 */
.compact-form {
  max-width: 1600px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-item-half {
  margin-bottom: 18px;
}

.form-item-half :deep(.el-input) {
  width: 100%;
}

/* Logo 预览 */
.logo-preview {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  margin-bottom: 18px;
}

.preview-label {
  font-size: var(--el-font-size-small);
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.preview-error {
  font-size: var(--el-font-size-small);
  color: var(--el-text-color-secondary);
}

/* 表单操作 */
.form-actions {
  margin-top: 8px;
  margin-bottom: 0;
}

.form-actions :deep(.el-button) {
  min-width: 120px;
}

/* JWT 提示样式 - 更紧凑 */
.jwt-alert {
  margin-bottom: 20px;
}

/* JWT 配置网格 */
.jwt-config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.jwt-config-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.jwt-config-item.full-width {
  grid-column: 1 / -1;
}

.config-label {
  font-size: var(--el-font-size-small);
  color: var(--el-text-color-secondary);
}

.config-value {
  font-size: var(--el-font-size-base);
  font-weight: var(--el-font-weight-medium);
  color: var(--el-text-color-primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .jwt-config-grid {
    grid-template-columns: 1fr;
  }

  .section-header {
    gap: 12px;
  }

  .section-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
}
</style>
