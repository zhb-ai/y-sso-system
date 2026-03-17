<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>
    
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 站点信息 -->
      <el-tab-pane label="站点信息" name="site">
        <el-card class="form-card">
          <el-form :model="siteSettings" ref="siteFormRef" label-position="top">
            <el-form-item label="系统名称" prop="system_name">
              <el-input
                v-model="siteSettings.system_name"
                placeholder="请输入系统名称"
                size="large"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item label="系统描述" prop="system_desc">
              <el-input
                v-model="siteSettings.system_desc"
                type="textarea"
                :rows="3"
                placeholder="请输入系统描述"
                size="large"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item label="系统 Logo URL" prop="system_logo">
              <el-input
                v-model="siteSettings.system_logo"
                placeholder="请输入系统 Logo 图片地址"
                size="large"
              />
              <div v-if="siteSettings.system_logo" style="margin-top: 8px">
                <el-image :src="siteSettings.system_logo" style="height: 40px" fit="contain">
                  <template #error>
                    <span style="font-size: var(--el-font-size-xs); color: var(--el-text-color-secondary)">图片加载失败</span>
                  </template>
                </el-image>
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleSaveSite" :loading="saveLoading" size="large">
                保存
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- JWT 认证（只读） -->
      <el-tab-pane label="JWT 认证" name="jwt">
        <el-card class="form-card">
          <el-alert
            title="JWT 配置为只读"
            description="JWT 配置来自 config/settings.yaml，如需修改请直接编辑配置文件并重启服务。"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 20px"
          />
          <el-descriptions :column="2" border>
            <el-descriptions-item label="JWT 密钥">
              <el-tag type="info">{{ jwtSettings.secret_key }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="签名算法">
              {{ jwtSettings.algorithm }}
            </el-descriptions-item>
            <el-descriptions-item label="Access Token 有效期">
              {{ jwtSettings.access_token_expire_minutes }} 分钟
            </el-descriptions-item>
            <el-descriptions-item label="Refresh Token 有效期">
              {{ jwtSettings.refresh_token_expire_days }} 天
            </el-descriptions-item>
            <el-descriptions-item label="滑动续期阈值">
              {{ jwtSettings.refresh_token_sliding_days }} 天
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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
.page-container {
  padding: 0 20px 20px;
}

.page-header {
  margin-bottom: 20px;
}

.settings-tabs {
  margin-top: 20px;
}

.form-card {
  margin-bottom: 20px;
}
</style>
