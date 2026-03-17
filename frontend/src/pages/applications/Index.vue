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
        v-loading="loading"
        :data="applications"
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="id" label="ID" width="80" align="center">
          <template #default="scope">
            <el-tag type="info" size="small" effect="plain">#{{ scope.row.id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="应用名称" min-width="200">
          <template #default="scope">
            <div class="app-info">
              <el-avatar :size="32" :src="scope.row.logo_url" class="app-logo">
                <el-icon><Document /></el-icon>
              </el-avatar>
              <div class="app-details">
                <div class="app-name">{{ scope.row.name }}</div>
                <div class="app-desc">{{ scope.row.description || '暂无描述' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="应用编码" min-width="150">
          <template #default="scope">
            <el-tag type="primary" size="small" effect="light">{{ scope.row.code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="client_id" label="客户端ID" min-width="220">
          <template #default="scope">
            <div class="copyable-field">
              <el-text class="client-id-text" truncated>{{ scope.row.client_id }}</el-text>
              <el-button size="small" type="primary" link @click="handleCopy(scope.row.client_id)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </div>
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
            <el-text class="time-text" size="small">{{ formatDate(scope.row.created_at) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" align="center" fixed="right" class-name="table-cell-flex-center">
          <template #default="scope">
            <el-button type="primary" size="small" link @click="handleEdit(scope.row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button type="success" size="small" link @click="handleResetSecret(scope.row)">
              <el-icon><RefreshRight /></el-icon> 密钥
            </el-button>
            <el-button type="danger" size="small" link @click="handleDelete(scope.row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
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
    
    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEditing ? '编辑应用' : '新建应用'"
      width="600px"
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
                    <el-input v-model="applicationForm.name" placeholder="请输入应用名称" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="应用编码" prop="code">
                    <el-input
                      v-model="applicationForm.code"
                      placeholder="字母、数字、下划线"
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
                />
              </el-form-item>
              <el-form-item label="重定向URI" prop="redirect_uris_str">
                <el-input
                  v-model="applicationForm.redirect_uris_str"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入重定向URI，多个URI用换行分隔"
                />
              </el-form-item>
              <el-form-item label="Logo URL" prop="logo_url">
                <el-input v-model="applicationForm.logo_url" placeholder="请输入应用Logo URL（可选）" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确认</el-button>
      </template>
    </el-dialog>
    
    <!-- 密钥展示对话框 -->
    <el-dialog
      v-model="secretDialogVisible"
      title="客户端凭证"
      width="700px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <el-alert
        title="请妥善保存以下凭证信息，客户端密钥仅显示一次！"
        type="warning"
        :closable="false"
        show-icon
        class="secret-alert"
      />
      
      <el-descriptions :column="1" border>
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
            <code class="secret-text secret-text--danger">{{ secretInfo.client_secret }}</code>
            <el-button size="small" type="primary" link @click="handleCopy(secretInfo.client_secret)">
              <el-icon><CopyDocument /></el-icon> 复制
            </el-button>
          </div>
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button type="primary" @click="secretDialogVisible = false">我已保存，关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, RefreshRight, Edit, Delete, Document, Check, Close, CopyDocument, Grid } from '@element-plus/icons-vue'
import { applicationApi } from '@/api'
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
  redirect_uris_str: '',
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
  ]
}

// 密钥展示对话框
const secretDialogVisible = ref(false)
const secretInfo = reactive({
  client_id: '',
  client_secret: ''
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

// 复制到剪贴板
const handleCopy = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
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
const handleCreate = () => {
  isEditing.value = false
  resetForm()
  formDialogVisible.value = true
}

// 编辑应用
const handleEdit = (row) => {
  isEditing.value = true
  applicationForm.id = row.id
  applicationForm.name = row.name
  applicationForm.code = row.code
  applicationForm.description = row.description || ''
  applicationForm.redirect_uris_str = Array.isArray(row.redirect_uris)
    ? row.redirect_uris.join('\n')
    : ''
  applicationForm.logo_url = row.logo_url || ''
  formDialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!applicationFormRef.value) return
  
  try {
    await applicationFormRef.value.validate()
    submitLoading.value = true
    
    // 转换重定向URI格式：换行分隔文本 → 数组
    const redirectUris = applicationForm.redirect_uris_str
      .split('\n')
      .map(uri => uri.trim())
      .filter(uri => uri)
    
    if (isEditing.value) {
      // 更新应用
      const updateData = {
        name: applicationForm.name,
        description: applicationForm.description || null,
        redirect_uris: redirectUris,
        logo_url: applicationForm.logo_url || null
      }
      await applicationApi.update(applicationForm.id, updateData)
      ElMessage.success('更新应用成功')
    } else {
      // 新建应用
      const createData = {
        name: applicationForm.name,
        code: applicationForm.code,
        description: applicationForm.description || null,
        redirect_uris: redirectUris,
        logo_url: applicationForm.logo_url || null
      }
      const response = await applicationApi.create(createData)
      
      // 创建成功后展示密钥信息
      const appData = response.data || {}
      secretInfo.client_id = appData.client_id || ''
      secretInfo.client_secret = appData.client_secret || ''
      secretDialogVisible.value = true
      
      ElMessage.success('创建应用成功')
    }
    
    formDialogVisible.value = false
    getApplications()
  } catch (error) {
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
      `确定要重置应用「${row.name}」的客户端密钥吗？此操作将生成新的密钥，旧密钥将立即失效。`,
      '重置密钥',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await applicationApi.resetSecret(row.id)
    
    // 展示新密钥
    const appData = response.data || {}
    secretInfo.client_id = appData.client_id || row.client_id
    secretInfo.client_secret = appData.client_secret || ''
    secretDialogVisible.value = true
    
    ElMessage.success('密钥已重置')
    getApplications()
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, getDefaultErrorMessage('reset'))
    }
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
  applicationForm.redirect_uris_str = ''
  applicationForm.logo_url = ''
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

// 初始化
onMounted(() => {
  getApplications()
})
</script>

<style scoped>
@import '../../styles/components/ui/tables.css';
@import '../../styles/components/ui/filters.css';

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
  font-size: var(--font-size-sm, 12px);
}

.secret-alert {
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
  font-size: 13px;
  padding: 4px 8px;
  background: var(--el-fill-color-light, #f5f7fa);
  border-radius: 4px;
  line-height: 1.6;
}

.secret-text--danger {
  color: var(--el-color-danger, #f56c6c);
}
</style>
