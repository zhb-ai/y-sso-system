<template>
  <div class="page-container">
    <div class="page-header">
      <h2>应用管理</h2>
      <el-button type="primary" class="btn-modern" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建应用
      </el-button>
    </div>
    
    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索应用名称或编码"
            clearable
            autocomplete="off"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filterStatus" placeholder="请选择状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="启用" value="true">
              <el-icon><Check /></el-icon> 启用
            </el-option>
            <el-option label="禁用" value="false">
              <el-icon><Close /></el-icon> 禁用
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" class="btn-modern" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button class="btn-reset" @click="handleReset">
            <el-icon><RefreshRight /></el-icon> 重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 数据表格 -->
    <el-card class="data-card" shadow="hover">
      <el-table
        v-if="applications.length > 0"
        v-loading="loading"
        :data="applications"
        style="width: 100%"
        row-key="id"
        tooltip-effect="light"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="应用名称" min-width="200">
          <template #default="scope">
            <div class="app-info">
              <el-avatar :size="32" :src="scope.row.logo_url" class="app-logo" alt="应用图标">
                <el-icon><Document /></el-icon>
              </el-avatar>
              <div class="app-details">
                <div class="app-name truncate">{{ scope.row.name }}</div>
                <div :title="scope.row.description || ''" class="app-desc line-clamp">{{ scope.row.description || '暂无描述' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="call_count_24h" label="24小时调用次数" width="130" align="center">
          <template #default="scope">
            {{ scope.row.call_count_24h || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="call_count_7d" label="一周调用次数" width="120" align="center">
          <template #default="scope">
            {{ scope.row.call_count_7d || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="code" label="应用编码" min-width="120" />
        <el-table-column prop="client_id" label="客户端ID" min-width="220">
          <template #default="scope">
            <div class="copyable-field">
              <span class="client-id-text">{{ scope.row.client_id }}</span>
              <el-button size="small" link @click="handleCopy(scope.row.client_id)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="client_type" label="客户端类型" width="100" align="center">
          <template #default="scope">
            <el-tag
              size="small"
              effect="light"
              :type="scope.row.client_type === 'public' ? 'warning' : 'success'"
            >
              {{ scope.row.client_type === 'public' ? '公开' : '机密' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="handleStatusChange(scope.row)"
              :active-action-icon="Check"
              :inactive-action-icon="Close"
              active-text="启用"
              inactive-text="禁用"
              inline-prompt
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" align="right">
          <template #default="scope">
            <el-button type="info" size="small" link @click="handleShowIntegrationConfig(scope.row)">
              <el-icon><Document /></el-icon> 对接配置
            </el-button>
            <el-button type="primary" size="small" link @click="handleEdit(scope.row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button size="small" link @click="handleResetSecret(scope.row)">
              <el-icon><RefreshRight /></el-icon> 密钥
            </el-button>
            <el-button size="small" link class="btn-delete" @click="handleDelete(scope.row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <EmptyState
        v-else-if="!loading"
        type="data"
        :icon="Collection"
        title="暂无应用"
        :description="searchKeyword || filterStatus ? '没有找到符合条件的应用，请调整搜索条件' : '还没有创建任何应用，点击下方按钮创建第一个应用'"
        :action-text="searchKeyword || filterStatus ? '重置筛选' : '新建应用'"
        :action-icon="searchKeyword || filterStatus ? RefreshRight : Plus"
        @action="searchKeyword || filterStatus ? handleReset() : handleCreate()"
      />

      <!-- 分页 -->
      <div class="pagination-container" v-if="applications.length > 0">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 新建/编辑抽屉 -->
    <el-drawer
      v-model="formDialogVisible"
      :title="isEditing ? '编辑应用' : '新建应用'"
      size="820px"
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0;">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Grid /></el-icon>
              <span>基本信息</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form
              :model="applicationForm"
              :rules="applicationRules"
              ref="applicationFormRef"
              label-width="100px"
            >
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="应用名称" prop="name">
                    <el-input v-model="applicationForm.name" placeholder="请输入应用名称" autocomplete="off" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="应用编码" prop="code">
                    <el-input
                      v-model="applicationForm.code"
                      placeholder="字母、数字、下划线"
                      autocomplete="off"
                      :disabled="isEditing"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="应用描述" prop="description">
                <el-input
                  v-model="applicationForm.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入应用描述"
                  autocomplete="off"
                />
              </el-form-item>
              <el-form-item label="客户端类型" prop="client_type">
                <el-radio-group v-model="applicationForm.client_type">
                  <el-radio value="confidential">机密客户端</el-radio>
                  <el-radio value="public">公开客户端</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-alert
                v-if="applicationForm.client_type === 'public'"
                title="公开客户端不使用 client_secret，授权码流程需配合 PKCE（S256）。"
                type="warning"
                :closable="false"
                show-icon
                class="integration-alert"
              />
              <el-form-item label="重定向URI" prop="redirect_uris_str">
                <el-input
                  v-model="applicationForm.redirect_uris_str"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入重定向URI，多个URI用换行分隔"
                  autocomplete="off"
                />
              </el-form-item>
              <el-form-item label="IP 白名单" prop="allowed_ip_cidrs_str">
                <el-input
                  v-model="applicationForm.allowed_ip_cidrs_str"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入允许访问 token/userinfo 的 IP 或 CIDR，多个条目用换行分隔；留空表示不限制"
                  autocomplete="off"
                />
              </el-form-item>
              <el-form-item label="Logo URL" prop="logo_url">
                <el-input v-model="applicationForm.logo_url" placeholder="请输入应用Logo URL（可选）" autocomplete="off" />
              </el-form-item>
              <el-form-item label="SSO 对接信息">
                <div v-loading="ssoConfigLoading" class="sso-config-panel">
                  <el-alert
                    :title="applicationForm.id ? '当前应用的主要对接信息已展示在下方，可直接复制给接入方。' : '创建成功后会自动生成客户端凭证，系统对接地址可先查看。'"
                    type="info"
                    :closable="false"
                    show-icon
                    class="integration-alert"
                  />
                  <div class="sso-config-toolbar">
                    <el-button type="primary" link @click="handleCopyPrimarySsoConfig">
                      <el-icon><CopyDocument /></el-icon> 复制主要信息
                    </el-button>
                    <el-button type="primary" link @click="handleCopyAllSsoConfig">
                      <el-icon><CopyDocument /></el-icon> 复制全部配置
                    </el-button>
                    <el-button type="primary" link @click="ssoConfigExpanded = !ssoConfigExpanded">
                      {{ ssoConfigExpanded ? '收起全部' : '展开全部' }}
                    </el-button>
                  </div>

                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="客户端类型">
                      <el-tag
                        size="small"
                        effect="light"
                        :type="ssoConfig.client_type === 'public' ? 'warning' : 'success'"
                      >
                        {{ formatClientTypeLabel(ssoConfig.client_type) }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="客户端 ID">
                      <div class="secret-field">
                        <code class="secret-text">{{ ssoConfig.client_id || '创建成功后自动生成' }}</code>
                        <el-button
                          size="small"
                          type="primary"
                          link
                          :disabled="!ssoConfig.client_id"
                          @click="handleCopy(ssoConfig.client_id)"
                        >
                          <el-icon><CopyDocument /></el-icon> 复制
                        </el-button>
                      </div>
                    </el-descriptions-item>
                    <el-descriptions-item label="Issuer URL">
                      <div class="secret-field">
                        <code class="secret-text">{{ ssoConfig.issuer || '-' }}</code>
                        <el-button size="small" type="primary" link :disabled="!ssoConfig.issuer" @click="handleCopy(ssoConfig.issuer)">
                          <el-icon><CopyDocument /></el-icon> 复制
                        </el-button>
                      </div>
                    </el-descriptions-item>
                    <el-descriptions-item label="Discovery URL">
                      <div class="secret-field">
                        <code class="secret-text">{{ ssoConfig.discovery_url || '-' }}</code>
                        <el-button size="small" type="primary" link :disabled="!ssoConfig.discovery_url" @click="handleCopy(ssoConfig.discovery_url)">
                          <el-icon><CopyDocument /></el-icon> 复制
                        </el-button>
                      </div>
                    </el-descriptions-item>
                  </el-descriptions>

                  <el-collapse-transition>
                    <div v-show="ssoConfigExpanded" class="sso-config-expanded">
                      <el-descriptions :column="1" border size="small">
                        <el-descriptions-item label="Authorization Endpoint">
                          <div class="secret-field">
                            <code class="secret-text">{{ ssoConfig.authorization_endpoint || '-' }}</code>
                            <el-button size="small" type="primary" link :disabled="!ssoConfig.authorization_endpoint" @click="handleCopy(ssoConfig.authorization_endpoint)">
                              <el-icon><CopyDocument /></el-icon> 复制
                            </el-button>
                          </div>
                        </el-descriptions-item>
                        <el-descriptions-item label="Token Endpoint">
                          <div class="secret-field">
                            <code class="secret-text">{{ ssoConfig.token_endpoint || '-' }}</code>
                            <el-button size="small" type="primary" link :disabled="!ssoConfig.token_endpoint" @click="handleCopy(ssoConfig.token_endpoint)">
                              <el-icon><CopyDocument /></el-icon> 复制
                            </el-button>
                          </div>
                        </el-descriptions-item>
                        <el-descriptions-item label="UserInfo Endpoint">
                          <div class="secret-field">
                            <code class="secret-text">{{ ssoConfig.userinfo_endpoint || '-' }}</code>
                            <el-button size="small" type="primary" link :disabled="!ssoConfig.userinfo_endpoint" @click="handleCopy(ssoConfig.userinfo_endpoint)">
                              <el-icon><CopyDocument /></el-icon> 复制
                            </el-button>
                          </div>
                        </el-descriptions-item>
                        <el-descriptions-item label="JWKS URI">
                          <div class="secret-field">
                            <code class="secret-text">{{ ssoConfig.jwks_uri || '当前未启用' }}</code>
                            <el-button size="small" type="primary" link :disabled="!ssoConfig.jwks_uri" @click="handleCopy(ssoConfig.jwks_uri)">
                              <el-icon><CopyDocument /></el-icon> 复制
                            </el-button>
                          </div>
                        </el-descriptions-item>
                        <el-descriptions-item label="Grant Types">
                          <span>{{ ssoConfig.grant_types_supported.length ? ssoConfig.grant_types_supported.join(', ') : '-' }}</span>
                        </el-descriptions-item>
                        <el-descriptions-item label="Scopes">
                          <span>{{ ssoConfig.scopes_supported.length ? ssoConfig.scopes_supported.join(', ') : '-' }}</span>
                        </el-descriptions-item>
                        <el-descriptions-item label="PKCE">
                          <span>{{ ssoConfig.client_type === 'public' ? '公开客户端必须启用（当前支持 S256）' : (ssoConfig.pkce_supported ? '可选，当前已支持' : '暂未支持') }}</span>
                        </el-descriptions-item>
                        <el-descriptions-item label="Token 签名算法">
                          <span>{{ ssoConfig.token_signing_algorithm || '-' }}</span>
                        </el-descriptions-item>
                      </el-descriptions>
                    </div>
                  </el-collapse-transition>
                </div>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ applicationForm.id ? '保存' : '创建并生成配置' }}
        </el-button>
      </template>
    </el-drawer>
    
    <!-- 密钥展示抽屉 -->
    <el-drawer
      v-model="secretDialogVisible"
      title="客户端凭证"
      size="820px"
      destroy-on-close
    >
      <el-alert
        :title="secretInfo.client_type === 'public' ? '当前应用为公开客户端，无需客户端密钥。请保存客户端 ID 并按 PKCE 方式接入。' : '请妥善保存以下凭证信息，客户端密钥仅显示一次！'"
        :type="secretInfo.client_type === 'public' ? 'info' : 'warning'"
        :closable="false"
        show-icon
        class="secret-alert"
      />
      
      <el-descriptions :column="1" border>
        <el-descriptions-item label="客户端类型">
          <el-tag
            size="small"
            effect="light"
            :type="secretInfo.client_type === 'public' ? 'warning' : 'success'"
          >
            {{ formatClientTypeLabel(secretInfo.client_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="客户端ID">
          <div class="secret-field">
            <code class="secret-text">{{ secretInfo.client_id }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(secretInfo.client_id)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="客户端密钥">
          <div class="secret-field">
            <code class="secret-text secret-text--danger">{{ secretInfo.client_secret || '无需密钥（公开客户端）' }}</code>
            <el-button size="small" type="primary" link :disabled="!secretInfo.client_secret" @click="handleCopy(secretInfo.client_secret)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button type="primary" @click="secretDialogVisible = false">我已保存，关闭</el-button>
      </template>
    </el-drawer>

    <!-- 第三方系统对接配置抽屉 -->
    <el-drawer
      v-model="integrationDialogVisible"
      title="第三方系统对接配置"
      size="820px"
      destroy-on-close
    >
      <el-alert
        title="以下信息可直接提供给第三方系统实施同学；客户端密钥仅在创建或重置时可见。"
        type="info"
        :closable="false"
        show-icon
        class="integration-alert"
      />

      <el-descriptions v-loading="integrationLoading" :column="1" border>
        <el-descriptions-item label="应用名称">
          <span>{{ integrationInfo.app_name }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="客户端类型">
          <el-tag
            size="small"
            effect="light"
            :type="integrationInfo.client_type === 'public' ? 'warning' : 'success'"
          >
            {{ formatClientTypeLabel(integrationInfo.client_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Issuer URL">
          <div class="secret-field">
            <code class="secret-text">{{ integrationInfo.issuer }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(integrationInfo.issuer)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="Discovery URL">
          <div class="secret-field">
            <code class="secret-text">{{ integrationInfo.discovery_url }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(integrationInfo.discovery_url)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="Authorization Endpoint">
          <div class="secret-field">
            <code class="secret-text">{{ integrationInfo.authorization_endpoint }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(integrationInfo.authorization_endpoint)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="Token Endpoint">
          <div class="secret-field">
            <code class="secret-text">{{ integrationInfo.token_endpoint }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(integrationInfo.token_endpoint)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="UserInfo Endpoint">
          <div class="secret-field">
            <code class="secret-text">{{ integrationInfo.userinfo_endpoint }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(integrationInfo.userinfo_endpoint)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="JWKS URI">
          <span>{{ integrationInfo.jwks_uri || '当前未启用' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="客户端 ID">
          <div class="secret-field">
            <code class="secret-text">{{ integrationInfo.client_id }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(integrationInfo.client_id)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="客户端密钥">
          <div class="secret-field">
            <code class="secret-text secret-text--danger">{{ integrationInfo.client_type === 'public' ? '无需密钥（公开客户端）' : (integrationInfo.client_secret || '当前列表不展示客户端密钥，如需重新获取请点击“密钥”按钮重置。') }}</code>
            <el-button
              size="small"
              type="primary"
              link
              :disabled="!integrationInfo.client_secret"
              @click="handleCopy(integrationInfo.client_secret)"
            >
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="Grant Types">
          <span>{{ integrationInfo.grant_types_supported.join(', ') }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="Scopes">
          <span>{{ integrationInfo.scopes_supported.join(', ') }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="PKCE">
          <span>{{ integrationInfo.client_type === 'public' ? '公开客户端必须启用（当前支持 S256）' : (integrationInfo.pkce_supported ? '可选，当前已支持' : '暂未支持') }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="Token 签名算法">
          <span>{{ integrationInfo.token_signing_algorithm }}</span>
        </el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="handleCopyIntegrationConfig">复制全部</el-button>
        <el-button type="primary" @click="integrationDialogVisible = false">关闭</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, RefreshRight, Edit, Delete, Document, Check, Close, CopyDocument, Grid, Collection } from '@element-plus/icons-vue'
import { applicationApi, configApi } from '@/api'
import EmptyState from '@/components/EmptyState.vue'
import { handleApiError, getDefaultErrorMessage } from '@/utils/errorHandler'

// 表格数据
const applications = ref([])
const loading = ref(false)

// 筛选条件
const searchKeyword = ref('')
const filterStatus = ref('')

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 新建/编辑对话框
const formDialogVisible = ref(false)
const isEditing = ref(false)
const submitLoading = ref(false)
const applicationFormRef = ref(null)
const applicationForm = reactive({
  id: null,
  name: '',
  code: '',
  description: '',
  client_type: 'confidential',
  redirect_uris_str: '',
  allowed_ip_cidrs_str: '',
  logo_url: ''
})

// 验证规则
const applicationRules = {
  name: [
    { required: true, message: '请输入应用名称', trigger: 'blur' },
    { min: 2, max: 50, message: '应用名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入应用编码', trigger: 'blur' },
    { min: 2, max: 30, message: '应用编码长度在 2 到 30 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '应用编码只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  client_type: [
    { required: true, message: '请选择客户端类型', trigger: 'change' }
  ]
}

// 密钥展示对话框
const secretDialogVisible = ref(false)
const secretInfo = reactive({
  client_id: '',
  client_secret: '',
  client_type: 'confidential'
})

const integrationDialogVisible = ref(false)
const integrationLoading = ref(false)
const integrationInfo = reactive({
  app_name: '',
  client_type: 'confidential',
  issuer: '',
  discovery_url: '',
  authorization_endpoint: '',
  token_endpoint: '',
  userinfo_endpoint: '',
  jwks_uri: '',
  client_id: '',
  client_secret: '',
  grant_types_supported: [],
  scopes_supported: [],
  pkce_supported: false,
  token_signing_algorithm: ''
})

const ssoConfigLoading = ref(false)
const ssoConfigExpanded = ref(false)
const ssoConfig = reactive({
  app_name: '',
  client_type: 'confidential',
  issuer: '',
  discovery_url: '',
  authorization_endpoint: '',
  token_endpoint: '',
  userinfo_endpoint: '',
  jwks_uri: '',
  client_id: '',
  grant_types_supported: [],
  scopes_supported: [],
  pkce_supported: false,
  token_signing_algorithm: ''
})

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatClientTypeLabel = (clientType) => (
  clientType === 'public' ? '公开客户端（public）' : '机密客户端（confidential）'
)

// 复制到剪贴板
const handleCopy = async (text) => {
  try {
    await navigator.clipboard.writeText(text || '')
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const resetSsoConfig = () => {
  ssoConfig.app_name = ''
  ssoConfig.client_type = applicationForm.client_type || 'confidential'
  ssoConfig.issuer = ''
  ssoConfig.discovery_url = ''
  ssoConfig.authorization_endpoint = ''
  ssoConfig.token_endpoint = ''
  ssoConfig.userinfo_endpoint = ''
  ssoConfig.jwks_uri = ''
  ssoConfig.client_id = ''
  ssoConfig.grant_types_supported = []
  ssoConfig.scopes_supported = []
  ssoConfig.pkce_supported = false
  ssoConfig.token_signing_algorithm = ''
}

const applyOauth2Endpoints = (data = {}) => {
  ssoConfig.issuer = data.issuer || ''
  ssoConfig.discovery_url = data.discovery_url || ''
  ssoConfig.authorization_endpoint = data.authorization_endpoint || ''
  ssoConfig.token_endpoint = data.token_endpoint || ''
  ssoConfig.userinfo_endpoint = data.userinfo_endpoint || ''
  ssoConfig.jwks_uri = data.jwks_uri || ''
  ssoConfig.grant_types_supported = data.grant_types_supported || []
  ssoConfig.scopes_supported = data.scopes_supported || []
  ssoConfig.pkce_supported = Boolean(data.pkce_supported)
  ssoConfig.token_signing_algorithm = data.token_signing_algorithm || ''
}

const loadBaseSsoConfig = async () => {
  ssoConfigLoading.value = true
  try {
    const response = await configApi.getOauth2Endpoints()
    applyOauth2Endpoints(response.data || {})
  } catch (error) {
    handleApiError(error, '获取 SSO 对接信息失败')
  } finally {
    ssoConfigLoading.value = false
  }
}

const buildPrimarySsoConfigLines = () => [
  `应用名称: ${ssoConfig.app_name || applicationForm.name || '-'}`,
  `客户端类型: ${formatClientTypeLabel(ssoConfig.client_type)}`,
  `客户端 ID: ${ssoConfig.client_id || '创建成功后自动生成'}`,
  `Issuer URL: ${ssoConfig.issuer || '-'}`,
  `Discovery URL: ${ssoConfig.discovery_url || '-'}`
]

const buildAllSsoConfigLines = () => [
  ...buildPrimarySsoConfigLines(),
  `Authorization Endpoint: ${ssoConfig.authorization_endpoint || '-'}`,
  `Token Endpoint: ${ssoConfig.token_endpoint || '-'}`,
  `UserInfo Endpoint: ${ssoConfig.userinfo_endpoint || '-'}`,
  `JWKS URI: ${ssoConfig.jwks_uri || '当前未启用'}`,
  `Grant Types: ${ssoConfig.grant_types_supported.length ? ssoConfig.grant_types_supported.join(', ') : '-'}`,
  `Scopes: ${ssoConfig.scopes_supported.length ? ssoConfig.scopes_supported.join(', ') : '-'}`,
  `PKCE: ${ssoConfig.pkce_supported ? '已支持' : '暂未支持'}`,
  `Token 签名算法: ${ssoConfig.token_signing_algorithm || '-'}`
]

const handleCopyPrimarySsoConfig = async () => {
  await handleCopy(buildPrimarySsoConfigLines().join('\n'))
}

const handleCopyAllSsoConfig = async () => {
  await handleCopy(buildAllSsoConfigLines().join('\n'))
}

const handleCopyIntegrationConfig = async () => {
  const lines = [
    `应用名称: ${integrationInfo.app_name}`,
    `客户端类型: ${formatClientTypeLabel(integrationInfo.client_type)}`,
    `Issuer URL: ${integrationInfo.issuer}`,
    `Discovery URL: ${integrationInfo.discovery_url}`,
    `Authorization Endpoint: ${integrationInfo.authorization_endpoint}`,
    `Token Endpoint: ${integrationInfo.token_endpoint}`,
    `UserInfo Endpoint: ${integrationInfo.userinfo_endpoint}`,
    `JWKS URI: ${integrationInfo.jwks_uri || '当前未启用'}`,
    `客户端 ID: ${integrationInfo.client_id}`,
    `客户端密钥: ${integrationInfo.client_type === 'public' ? '无需密钥（公开客户端）' : (integrationInfo.client_secret || '当前列表不展示，需通过重置密钥重新获取')}`,
    `Grant Types: ${integrationInfo.grant_types_supported.join(', ')}`,
    `Scopes: ${integrationInfo.scopes_supported.join(', ')}`,
    `PKCE: ${integrationInfo.client_type === 'public' ? '公开客户端必须启用（当前支持 S256）' : (integrationInfo.pkce_supported ? '可选，当前已支持' : '暂未支持')}`,
    `Token 签名算法: ${integrationInfo.token_signing_algorithm}`
  ]
  await handleCopy(lines.join('\n'))
}

// 获取应用列表
const getApplications = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      keyword: searchKeyword.value || undefined,
      is_active: filterStatus.value === '' ? undefined : filterStatus.value
    }
    const response = await applicationApi.list(params)
    // 后端返回统一的 PageResponse 格式: { message, data: { rows, total_records, page, page_size } }
    const data = response.data || {}
    applications.value = data.rows || []
    pagination.total = data.total_records || 0
  } catch (error) {
    handleApiError(error, getDefaultErrorMessage('get'))
    applications.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 新建应用
const handleCreate = async () => {
  isEditing.value = false
  resetForm()
  formDialogVisible.value = true
  ssoConfigExpanded.value = false
  await loadBaseSsoConfig()
}

// 编辑应用
const handleEdit = async (row) => {
  isEditing.value = true
  applicationForm.id = row.id
  applicationForm.name = row.name
  applicationForm.code = row.code
  applicationForm.description = row.description || ''
  applicationForm.client_type = row.client_type || 'confidential'
  applicationForm.redirect_uris_str = Array.isArray(row.redirect_uris)
    ? row.redirect_uris.join('\n')
    : ''
  applicationForm.allowed_ip_cidrs_str = Array.isArray(row.allowed_ip_cidrs)
    ? row.allowed_ip_cidrs.join('\n')
    : ''
  applicationForm.logo_url = row.logo_url || ''
  formDialogVisible.value = true
  ssoConfigExpanded.value = false
  resetSsoConfig()
  ssoConfig.client_type = applicationForm.client_type
  ssoConfig.client_id = row.client_id || ''
  await loadBaseSsoConfig()
}

// 提交表单
const handleSubmit = async () => {
  if (!applicationFormRef.value) return
  
  // 先进行表单校验，校验失败直接返回，不进入后续逻辑
  const isValid = await applicationFormRef.value.validate().catch(() => false)
  if (!isValid) return
  
  submitLoading.value = true
  
  try {
    // 转换重定向URI格式：换行分隔文本 → 数组
    const redirectUris = applicationForm.redirect_uris_str
      .split('\n')
      .map(uri => uri.trim())
      .filter(uri => uri)
    const allowedIpCidrs = applicationForm.allowed_ip_cidrs_str
      .split('\n')
      .map(entry => entry.trim())
      .filter(entry => entry)
    
    if (isEditing.value) {
      // 更新应用
      const updateData = {
        name: applicationForm.name,
        description: applicationForm.description || null,
        client_type: applicationForm.client_type,
        redirect_uris: redirectUris,
        allowed_ip_cidrs: allowedIpCidrs,
        logo_url: applicationForm.logo_url || null
      }
      await applicationApi.update(applicationForm.id, updateData)
      ElMessage.success('更新应用成功')
      formDialogVisible.value = false
    } else {
      // 新建应用
      const createData = {
        name: applicationForm.name,
        code: applicationForm.code,
        description: applicationForm.description || null,
        client_type: applicationForm.client_type,
        redirect_uris: redirectUris,
        allowed_ip_cidrs: allowedIpCidrs,
        logo_url: applicationForm.logo_url || null
      }
      const response = await applicationApi.create(createData)

      // 创建成功后在当前弹窗中直接展示对接信息和密钥
      const appData = response.data || {}
      applicationForm.id = appData.id || null
      applicationForm.code = appData.code || applicationForm.code
      applicationForm.client_type = appData.client_type || applicationForm.client_type
      isEditing.value = true
      ssoConfig.client_type = appData.client_type || applicationForm.client_type
      ssoConfig.client_id = appData.client_id || ''
      ssoConfigExpanded.value = true

      ElMessage.success('创建应用成功，已生成 SSO 对接信息')
    }

    await getApplications()
  } catch (error) {
    console.error('提交应用表单失败:', error)
    const operation = isEditing.value ? 'update' : 'create'
    handleApiError(error, getDefaultErrorMessage(operation))
  } finally {
    submitLoading.value = false
  }
}

// 重置密钥
const handleResetSecret = async (row) => {
  try {
    await ElMessageBox.confirm(
      row.client_type === 'public'
        ? `应用「${row.name}」当前为公开客户端，无需客户端密钥。确认继续查看当前客户端配置吗？`
        : `确定要重置应用「${row.name}」的客户端密钥吗？此操作将生成新的密钥，旧密钥将立即失效。`,
      '重置密钥',
      {
        confirmButtonText: row.client_type === 'public' ? '继续查看' : '确定重置',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await applicationApi.resetSecret(row.id)
    
    // 展示新密钥
    const appData = response.data || {}
    secretInfo.client_id = appData.client_id || row.client_id
    secretInfo.client_secret = appData.client_secret || ''
    secretInfo.client_type = appData.client_type || row.client_type || 'confidential'
    secretDialogVisible.value = true
    
    ElMessage.success(secretInfo.client_type === 'public' ? '公开客户端无需密钥，已展示当前配置' : '密钥已重置')
    getApplications()
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, getDefaultErrorMessage('reset'))
    }
  }
}

const handleShowIntegrationConfig = async (row) => {
  integrationDialogVisible.value = true
  integrationLoading.value = true

  try {
    const response = await configApi.getOauth2Endpoints()
    const data = response.data || {}

    integrationInfo.app_name = row.name || ''
    integrationInfo.client_type = row.client_type || 'confidential'
    integrationInfo.issuer = data.issuer || ''
    integrationInfo.discovery_url = data.discovery_url || ''
    integrationInfo.authorization_endpoint = data.authorization_endpoint || ''
    integrationInfo.token_endpoint = data.token_endpoint || ''
    integrationInfo.userinfo_endpoint = data.userinfo_endpoint || ''
    integrationInfo.jwks_uri = data.jwks_uri || ''
    integrationInfo.client_id = row.client_id || ''
    integrationInfo.client_secret = ''
    integrationInfo.grant_types_supported = data.grant_types_supported || []
    integrationInfo.scopes_supported = data.scopes_supported || []
    integrationInfo.pkce_supported = Boolean(data.pkce_supported)
    integrationInfo.token_signing_algorithm = data.token_signing_algorithm || ''
  } catch (error) {
    integrationDialogVisible.value = false
    handleApiError(error, '获取对接配置失败')
  } finally {
    integrationLoading.value = false
  }
}

// 删除应用
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除应用「${row.name}」吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await applicationApi.delete(row.id)
    ElMessage.success('删除应用成功')
    getApplications()
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, getDefaultErrorMessage('delete'))
    }
  }
}

// 状态切换
const handleStatusChange = async (row) => {
  try {
    if (row.is_active) {
      await applicationApi.enable(row.id)
      ElMessage.success('启用应用成功')
    } else {
      await applicationApi.disable(row.id)
      ElMessage.success('禁用应用成功')
    }
  } catch (error) {
    handleApiError(error, '状态切换失败')
    // 恢复原状态
    row.is_active = !row.is_active
  }
}

// 重置表单
const resetForm = () => {
  applicationForm.id = null
  applicationForm.name = ''
  applicationForm.code = ''
  applicationForm.description = ''
  applicationForm.client_type = 'confidential'
  applicationForm.redirect_uris_str = ''
  applicationForm.allowed_ip_cidrs_str = ''
  applicationForm.logo_url = ''
  resetSsoConfig()
  ssoConfigExpanded.value = false
  if (applicationFormRef.value) {
    applicationFormRef.value.resetFields()
  }
}

// 搜索
const handleSearch = () => {
  pagination.currentPage = 1
  getApplications()
}

// 重置筛选条件
const handleReset = () => {
  searchKeyword.value = ''
  filterStatus.value = ''
  pagination.currentPage = 1
  getApplications()
}

// 分页大小变化
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  getApplications()
}

// 当前页码变化
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  getApplications()
}

watch(() => applicationForm.name, (value) => {
  ssoConfig.app_name = value || ''
})

watch(() => applicationForm.client_type, (value) => {
  ssoConfig.client_type = value || 'confidential'
})

// 初始化
onMounted(() => {
  getApplications()
})
</script>

<style scoped>

/* 删除按钮样式 - 默认无颜色，hover 显示 danger 色 */
.btn-delete {
  transition: color 0.2s ease;
}

.btn-delete:hover {
  color: var(--el-color-danger) !important;
}

.app-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.app-details {
  overflow: hidden;
}

.app-name {
  font-weight: var(--el-font-weight-bold);
  line-height: var(--c-line-height-sm);
}

.app-desc {
  font-size: var(--el-font-size-xs);
  color: var(--text-muted, #909399);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copyable-field {
  display: flex;
  align-items: center;
  gap: 4px;
}

.client-id-text {
  font-family: 'Courier New', Courier, monospace;
  word-break: break-all;
}

.secret-alert {
  margin-bottom: 1rem;
}

.integration-alert {
  margin-bottom: 1rem;
}

.secret-field {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.secret-text {
  flex: 1;
  word-break: break-all;
  font-family: 'Courier New', Courier, monospace;
  font-size: var(--el-font-size-sm);
  padding: 4px 8px;
  background: var(--el-fill-color-light, #f5f7fa);
  border-radius: 4px;
  line-height: var(--c-line-height-lg);
}

.secret-text--danger {
  color: var(--el-color-danger, #f56c6c);
}

.sso-config-panel {
  width: 100%;
}

.sso-config-toolbar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.sso-config-expanded {
  margin-top: 12px;
}

/* 文本溢出处理 */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 应用信息布局 */
.app-details {
  min-width: 0;
  flex: 1;
}

/* 表格容器横向滚动 */
.data-card :deep(.el-card__body) {
  overflow-x: auto;
}


</style>
