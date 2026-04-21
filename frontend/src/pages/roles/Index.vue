<template>
  <div class="page-container">
    <div class="page-header">
      <h2>角色管理</h2>
      <el-button type="primary" class="btn-modern" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建角色
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-card class="data-card" shadow="hover">
      <el-table
        v-if="roles.length > 0"
        v-loading="loading"
        :data="roles"
        style="width: 100%"
        row-key="id"
        tooltip-effect="light"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="code" label="角色编码" min-width="120" />
        <el-table-column prop="description" label="角色描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340" align="right" fixed="right" class-name="table-cell-flex-end">
          <template #default="scope">
            <el-button size="small" link @click="handleEdit(scope.row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button size="small" link @click="handlePermissions(scope.row)">
              <el-icon><Key /></el-icon> 权限
            </el-button>
            <el-button size="small" link @click="handleViewUsers(scope.row)">
              <el-icon><User /></el-icon> 用户
            </el-button>
            <el-button
              size="small"
              link
              class="btn-delete"
              :disabled="isSystemRole(scope.row.code)"
              @click="handleDelete(scope.row)"
            >
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
        title="暂无角色"
        description="角色用于定义用户的权限集合，创建角色后可以为用户分配相应的权限"
        action-text="新建角色"
        :action-icon="Plus"
        @action="handleCreate"
      />
    </el-card>

    <!-- 创建/编辑角色对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑角色' : '新建角色'"
      width="500px"
      align-center
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0;">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Medal /></el-icon>
              <span>基本信息</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="roleForm" :rules="roleRules" ref="roleFormRef" label-width="80px">
              <el-form-item label="角色编码" prop="code">
                <el-input
                  v-model="roleForm.code"
                  placeholder="如 admin, editor"
                  :disabled="isEdit"
                />
              </el-form-item>
              <el-form-item label="角色名称" prop="name">
                <el-input v-model="roleForm.name" placeholder="如 管理员" autocomplete="off" />
              </el-form-item>
              <el-form-item label="描述" prop="description">
                <el-input v-model="roleForm.description" type="textarea" :rows="3" placeholder="角色描述（选填）" autocomplete="off" />
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

    <!-- 角色用户列表抽屉 -->
    <el-drawer
      v-model="usersDialogVisible"
      :title="`${currentRole && currentRole.name}（${currentRole && currentRole.code}）- 关联用户`"
      size="800px"
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0;">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><User /></el-icon>
              <span>用户列表</span>
            </div>
          </div>
          <div class="section-block__table">
            <el-table v-loading="usersLoading" :data="roleUsers" size="small">
              <el-table-column prop="id" label="ID" width="70" align="center" />
              <el-table-column prop="username" label="用户名" min-width="110" />
              <el-table-column prop="name" label="姓名" min-width="90" />
              <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
              <el-table-column label="所有角色" min-width="160">
                <template #default="scope">
                  <span v-for="(role, index) in scope.row.roles" :key="role">
                    {{ role }}{{ index < scope.row.roles.length - 1 ? '、' : '' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" align="right">
                <template #default="scope">
                  <el-button
                    size="small"
                    link
                    class="btn-delete"
                    @click="handleRemoveUserRole(scope.row)"
                  >
                    <el-icon><Remove /></el-icon> 移除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="usersDialogVisible = false">关闭</el-button>
      </template>
    </el-drawer>

    <!-- 权限分配抽屉 -->
    <el-drawer
      v-model="permDrawerVisible"
      :title="`${permRole && permRole.name}（${permRole && permRole.code}）- 分配权限`"
      size="520px"
      destroy-on-close
    >
      <div class="perm-drawer-content">
        <!-- 操作栏 -->
        <div class="perm-drawer-toolbar">
          <el-button size="small" type="primary" plain :loading="scanLoading" @click="handleScan">
            <el-icon><Refresh /></el-icon> 扫描路由更新权限
          </el-button>
          <el-alert
            v-if="permRole && permRole.code === 'admin'"
            title="admin 角色自动拥有所有权限"
            type="info"
            :closable="false"
            show-icon
            style="flex: 1; padding: 6px 12px;"
          />
        </div>

        <!-- 权限列表 -->
        <div class="perm-drawer-body" v-loading="permLoading">
          <template v-if="permTree.length > 0">
            <!-- 全选区域 -->
            <div class="perm-select-all">
              <el-checkbox
                v-model="checkAll"
                :indeterminate="isIndeterminate"
                @change="handleCheckAllChange"
              >全选所有权限</el-checkbox>
              <el-text type="info" size="small">已选 {{ checkedPermIds.length }} 项</el-text>
            </div>

            <!-- 权限分组 -->
            <div class="perm-groups">
              <div v-for="group in permTree" :key="group.module" class="perm-group">
                <div class="perm-group-header">
                  <span class="perm-group-name">{{ group.module }}</span>
                  <el-text type="info" size="small">{{ group.permissions.length }} 项</el-text>
                </div>
                <el-checkbox-group v-model="checkedPermIds" class="perm-checkbox-group">
                  <el-checkbox
                    v-for="perm in group.permissions"
                    :key="perm.id"
                    :value="perm.id"
                    :label="perm.name"
                    :disabled="permRole && permRole.code === 'admin'"
                    class="perm-checkbox"
                  >
                    <div class="perm-checkbox-content">
                      <span class="perm-name">{{ perm.name }}</span>
                      <el-text type="info" size="small" class="perm-code">{{ perm.code }}</el-text>
                    </div>
                  </el-checkbox>
                </el-checkbox-group>
              </div>
            </div>
          </template>
          <div v-else class="perm-empty">
            <el-empty description="暂无权限数据" :image-size="80">
              <template #description>
                <div style="text-align: center;">
                  <p>暂无权限数据</p>
                  <p style="color: var(--el-text-color-secondary); font-size: var(--el-font-size-small); margin-top: 8px;">请先点击上方「扫描路由更新权限」按钮</p>
                </div>
              </template>
            </el-empty>
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="perm-drawer-footer">
          <el-button @click="permDrawerVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="permSaving"
            :disabled="permRole && permRole.code === 'admin'"
            @click="handleSavePermissions"
          >保存</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, User, Key, Refresh, Remove, Medal, Collection } from '@element-plus/icons-vue'
import { roleApi, permissionApi } from '@/api'
import { handleApiError, getDefaultErrorMessage } from '@/utils/errorHandler'
import EmptyState from '@/components/EmptyState.vue'

// ==================== 角色列表 ====================

const roles = ref([])
const loading = ref(false)

const getRoles = async () => {
  loading.value = true
  try {
    const response = await roleApi.list()
    roles.value = response.data || []
  } catch (error) {
    handleApiError(error, getDefaultErrorMessage('get'))
    roles.value = []
  } finally {
    loading.value = false
  }
}

// 系统内置角色不可删除
const isSystemRole = (code) => ['admin', 'user', 'external'].includes(code)

// ==================== 创建 / 编辑 ====================

const formDialogVisible = ref(false)
const formLoading = ref(false)
const isEdit = ref(false)
const roleFormRef = ref(null)

const roleForm = reactive({
  code: '',
  name: '',
  description: '',
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
  roleForm.code = ''
  roleForm.name = ''
  roleForm.description = ''
  formDialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  roleForm.code = row.code
  roleForm.name = row.name
  roleForm.description = row.description || ''
  formDialogVisible.value = true
}

const handleFormSubmit = async () => {
  if (!roleFormRef.value) return
  try {
    await roleFormRef.value.validate()
    formLoading.value = true

    if (isEdit.value) {
      await roleApi.update(roleForm.code, {
        name: roleForm.name,
        description: roleForm.description,
      })
      ElMessage.success('角色更新成功')
    } else {
      await roleApi.create({
        code: roleForm.code,
        name: roleForm.name,
        description: roleForm.description,
      })
      ElMessage.success('角色创建成功')
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
      `确定要删除角色「${row.name}」(${row.code}) 吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await roleApi.delete(row.code)
    ElMessage.success('删除成功')
    getRoles()
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, getDefaultErrorMessage('delete'))
    }
  }
}

// ==================== 查看角色用户 ====================

const usersDialogVisible = ref(false)
const usersLoading = ref(false)
const currentRole = ref(null)
const roleUsers = ref([])

const handleViewUsers = async (row) => {
  currentRole.value = row
  usersDialogVisible.value = true
  usersLoading.value = true
  try {
    const response = await roleApi.users(row.code)
    roleUsers.value = response.data || []
  } catch (error) {
    handleApiError(error, '获取用户列表失败')
    roleUsers.value = []
  } finally {
    usersLoading.value = false
  }
}

const handleRemoveUserRole = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要将用户「${user.username}」从角色「${currentRole.value.name}」中移除吗？`,
      '确认移除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await roleApi.unassignRole({
      user_id: user.id,
      role_code: currentRole.value.code,
    })
    ElMessage.success('已移除')
    // 刷新当前弹窗的用户列表
    const response = await roleApi.users(currentRole.value.code)
    roleUsers.value = response.data || []
  } catch (error) {
    if (error !== 'cancel') {
      handleApiError(error, '移除失败')
    }
  }
}

// ==================== 权限分配 ====================

const permDrawerVisible = ref(false)
const permLoading = ref(false)
const permSaving = ref(false)
const scanLoading = ref(false)
const permRole = ref(null)
const permTree = ref([])           // [{module, permissions: [{id, code, name, ...}]}]
const checkedPermIds = ref([])     // 当前勾选的权限 ID 列表
const allPermIds = computed(() => {
  const ids = []
  for (const g of permTree.value) {
    for (const p of g.permissions) {
      ids.push(p.id)
    }
  }
  return ids
})

// 全选 / 半选状态
const checkAll = computed({
  get: () => allPermIds.value.length > 0 && checkedPermIds.value.length === allPermIds.value.length,
  set: () => {},
})
const isIndeterminate = computed(() =>
  checkedPermIds.value.length > 0 && checkedPermIds.value.length < allPermIds.value.length
)

const handleCheckAllChange = (val) => {
  checkedPermIds.value = val ? [...allPermIds.value] : []
}

// 打开权限分配抽屉
const handlePermissions = async (row) => {
  permRole.value = row
  permDrawerVisible.value = true
  permLoading.value = true
  try {
    // 并行加载：权限树 + 角色已分配权限
    const [treeRes, rolePermRes] = await Promise.all([
      permissionApi.tree(),
      permissionApi.getRolePermissions(row.code),
    ])
    permTree.value = treeRes.data || []
    const assignedIds = (rolePermRes.data || []).map(p => p.id)
    checkedPermIds.value = assignedIds
  } catch (error) {
    handleApiError(error, '加载权限数据失败')
  } finally {
    permLoading.value = false
  }
}

// 扫描路由
const handleScan = async () => {
  scanLoading.value = true
  try {
    const res = await permissionApi.scan()
    ElMessage.success(res.message || '扫描完成')
    // 刷新权限树
    const treeRes = await permissionApi.tree()
    permTree.value = treeRes.data || []
  } catch (error) {
    handleApiError(error, '扫描失败')
  } finally {
    scanLoading.value = false
  }
}

// 保存权限
const handleSavePermissions = async () => {
  permSaving.value = true
  try {
    await permissionApi.setRolePermissions(permRole.value.code, checkedPermIds.value)
    ElMessage.success('权限保存成功')
    permDrawerVisible.value = false
  } catch (error) {
    handleApiError(error, '保存失败')
  } finally {
    permSaving.value = false
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

.perm-group {
  margin-bottom: 16px;
}

.perm-group-title {
  font-weight: var(--el-font-weight-extra-bold);
  font-size: var(--el-font-size-base);
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
  border-left: 3px solid var(--el-color-primary);
  padding-left: 8px;
}

/* 权限抽屉样式 */
.perm-drawer-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  gap: 16px;
}

.perm-drawer-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.perm-drawer-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 16px;
}

.perm-select-all {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-radius: 6px;
  margin-bottom: 16px;
  border: 1px solid var(--el-border-color-lighter);
}

.perm-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.perm-group {
  background: var(--el-bg-color);
  border-radius: 6px;
  padding: 12px 16px;
  border: 1px solid var(--el-border-color-lighter);
}

.perm-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.perm-group-name {
  font-weight: var(--el-font-weight-bold);
  font-size: var(--el-font-size-base);
  color: var(--el-text-color-primary);
}

.perm-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.perm-checkbox {
  margin: 0;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.perm-checkbox:hover {
  background-color: var(--el-fill-color);
}

.perm-checkbox-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.perm-name {
  font-size: var(--el-font-size-base);
  color: var(--el-text-color-primary);
}

.perm-code {
  font-size: var(--el-font-size-small);
}

.perm-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.perm-drawer-footer {
  flex-shrink: 0;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
