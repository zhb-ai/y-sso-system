<template>
  <div class="page-container">
    <div class="page-header">
      <h2>SSO 角色管理</h2>
      <el-button type="primary" class="btn-modern" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建 SSO 角色
      </el-button>
    </div>

    <el-alert
      type="info"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
    >
      <template #title>
        SSO 角色用于同步给外部系统，与系统内部角色（管理员/用户/外部用户）相互独立。
        外部系统通过 OAuth2 接口获取用户的 SSO 角色列表。
        在「用户管理」页面可为用户分配 SSO 角色。
      </template>
    </el-alert>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索角色名称或编码"
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
            <el-option label="启用" value="active">
              <el-icon><Check /></el-icon> 启用
            </el-option>
            <el-option label="禁用" value="inactive">
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
        v-if="filteredRoles.length > 0"
        v-loading="loading"
        :data="filteredRoles"
        style="width: 100%"
        row-key="id"
        tooltip-effect="dark"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="code" label="角色编码" min-width="140" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="scope">
            <span v-if="scope.row.is_active">启用</span>
            <span v-else class="status-danger">禁用</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="right" fixed="right" class-name="table-cell-flex-end">
          <template #default="scope">
            <el-button size="small" link @click="handleEdit(scope.row)">
              <el-icon><Edit /></el-icon> 编辑
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
        title="暂无 SSO 角色"
        :description="searchKeyword || filterStatus ? '没有找到符合条件的角色，请调整搜索条件' : '还没有创建任何 SSO 角色，点击下方按钮创建第一个角色'"
        :action-text="searchKeyword || filterStatus ? '重置筛选' : '新建角色'"
        :action-icon="searchKeyword || filterStatus ? RefreshRight : Plus"
        @action="searchKeyword || filterStatus ? handleReset() : handleCreate()"
      />
    </el-card>

    <!-- 创建/编辑 SSO 角色对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑 SSO 角色' : '新建 SSO 角色'"
      width="500px"
      align-center
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0;">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Connection /></el-icon>
              <span>基本信息</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="roleForm" :rules="roleRules" ref="roleFormRef" label-width="80px">
              <el-form-item label="角色编码" prop="code">
                <el-input
                  v-model="roleForm.code"
                  placeholder="如 finance_admin, hr_viewer"
                  :disabled="isEdit"
                />
              </el-form-item>
              <el-form-item label="角色名称" prop="name">
                <el-input v-model="roleForm.name" placeholder="如 财务管理员" autocomplete="off" />
              </el-form-item>
              <el-form-item label="描述" prop="description">
                <el-input v-model="roleForm.description" type="textarea" :rows="3" placeholder="角色描述（选填）" autocomplete="off" />
              </el-form-item>
              <el-form-item label="排序" prop="sort_order">
                <el-input-number v-model="roleForm.sort_order" :min="0" :max="9999" style="width: 120px" />
              </el-form-item>
              <el-form-item v-if="isEdit" label="状态" prop="is_active">
                <el-switch
                  v-model="roleForm.is_active"
                  :active-action-icon="Check"
                  :inactive-action-icon="Close"
                  active-text="启用"
                  inactive-text="禁用"
                  inline-prompt
                />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleFormSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ssoRoleApi } from '@/api'
import { handleApiError, getDefaultErrorMessage } from '@/utils/errorHandler'
import { Plus, Edit, Delete, Search, RefreshRight, Check, Close, Connection, Collection } from '@element-plus/icons-vue'
import EmptyState from '@/components/EmptyState.vue'

// ==================== 筛选条件 ====================

const searchKeyword = ref('')
const filterStatus = ref('')

const handleSearch = () => {
  // 客户端过滤，无需重新请求
}

const handleReset = () => {
  searchKeyword.value = ''
  filterStatus.value = ''
}

// ==================== SSO 角色列表 ====================

const roles = ref([])
const loading = ref(false)

const filteredRoles = computed(() => {
  let result = roles.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(r =>
      (r.name || '').toLowerCase().includes(kw) ||
      (r.code || '').toLowerCase().includes(kw)
    )
  }
  if (filterStatus.value === 'active') {
    result = result.filter(r => r.is_active)
  } else if (filterStatus.value === 'inactive') {
    result = result.filter(r => !r.is_active)
  }
  return result
})

const getRoles = async () => {
  loading.value = true
  try {
    const response = await ssoRoleApi.list()
    roles.value = response.data || []
  } catch (error) {
    handleApiError(error, getDefaultErrorMessage('get'))
    roles.value = []
  } finally {
    loading.value = false
  }
}

// ==================== 创建 / 编辑 ====================

const formDialogVisible = ref(false)
const formLoading = ref(false)
const isEdit = ref(false)
const roleFormRef = ref(null)
const editingCode = ref('')

const roleForm = reactive({
  code: '',
  name: '',
  description: '',
  sort_order: 0,
  is_active: true,
})

const roleRules = {
  code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '编码只能包含小写字母、数字和下划线，且以字母开头', trigger: 'blur' },
  ],
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
  ],
}

const handleCreate = () => {
  isEdit.value = false
  editingCode.value = ''
  roleForm.code = ''
  roleForm.name = ''
  roleForm.description = ''
  roleForm.sort_order = 0
  roleForm.is_active = true
  formDialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editingCode.value = row.code
  roleForm.code = row.code
  roleForm.name = row.name
  roleForm.description = row.description || ''
  roleForm.sort_order = row.sort_order || 0
  roleForm.is_active = row.is_active
  formDialogVisible.value = true
}

const handleFormSubmit = async () => {
  if (!roleFormRef.value) return
  
  // 先进行表单校验，校验失败直接返回，不进入后续逻辑
  const isValid = await roleFormRef.value.validate().catch(() => false)
  if (!isValid) return
  
  formLoading.value = true

  try {
    if (isEdit.value) {
      await ssoRoleApi.update(editingCode.value, {
        name: roleForm.name,
        description: roleForm.description,
        sort_order: roleForm.sort_order,
        is_active: roleForm.is_active,
      })
      ElMessage.success('SSO 角色更新成功')
    } else {
      await ssoRoleApi.create({
        code: roleForm.code,
        name: roleForm.name,
        description: roleForm.description,
        sort_order: roleForm.sort_order,
      })
      ElMessage.success('SSO 角色创建成功')
    }

    formDialogVisible.value = false
    getRoles()
  } catch (error) {
    handleApiError(error, isEdit.value ? '更新失败' : '创建失败')
  } finally {
    formLoading.value = false
  }
}

// ==================== 删除 ====================

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 SSO 角色「${row.name}」(${row.code}) 吗？已分配给用户的该角色将同时被移除。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await ssoRoleApi.delete(row.code)
    ElMessage.success('删除成功')
    getRoles()
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, getDefaultErrorMessage('delete'))
    }
  }
}

// ==================== 工具方法 ====================

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

// ==================== 初始化 ====================

onMounted(() => {
  getRoles()
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
</style>
