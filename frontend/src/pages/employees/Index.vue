<template>
  <div class="page-container">
    <div class="page-header">
      <h2>员工管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建员工
      </el-button>
    </div>
    
    <!-- 筛选 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="组织">
          <el-select v-model="filter.org_id" placeholder="全部组织" clearable @change="handleSearch">
            <el-option v-for="org in organizations" :key="org.id" :label="org.name" :value="org.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filter.keyword" placeholder="姓名/手机号" clearable @keyup.enter="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item label="雇佣状态">
          <el-select v-model="filter.emp_status" placeholder="全部" clearable @change="handleSearch" style="width: 110px">
            <el-option label="在职" :value="3" />
            <el-option label="试用期" :value="2" />
            <el-option label="待入职" :value="1" />
            <el-option label="停职" :value="0" />
            <el-option label="离职" :value="-1" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号状态">
          <el-select v-model="filter.account_status" placeholder="全部" clearable @change="handleSearch" style="width: 110px">
            <el-option label="已激活" :value="1" />
            <el-option label="未激活" :value="0" />
            <el-option label="已禁用" :value="-1" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshRight /></el-icon> 重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 员工列表 -->
    <el-card class="data-card" shadow="hover">
      <el-table v-loading="loading" :data="employees" style="width: 100%">
        <el-table-column prop="name" label="姓名" min-width="100">
          <template #default="{ row }">
            <div class="employee-info">
              <el-avatar :size="32" class="avatar">{{ row.name?.charAt(0) }}</el-avatar>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="员工编码" min-width="100" />
        <el-table-column prop="mobile" label="手机号" min-width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="性别" width="70">
          <template #default="{ row }">
            {{ row.gender === 1 ? '男' : row.gender === 2 ? '女' : '未知' }}
          </template>
        </el-table-column>
        <el-table-column prop="primary_org_name" label="主组织" min-width="100">
          <template #default="{ row }">
            <el-tag v-if="row.primary_org_name" type="success" size="small">{{ row.primary_org_name }}</el-tag>
            <el-tag v-else type="info" size="small">未分配</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="primary_dept_name" label="主部门" min-width="100">
          <template #default="{ row }">
            <el-tag v-if="row.primary_dept_name" size="small">{{ row.primary_dept_name }}</el-tag>
            <el-tag v-else type="info" size="small">未分配</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="雇佣状态" width="110" align="center" class-name="table-cell-flex-center-offset">
          <template #default="{ row }">
            <template v-if="row.emp_status !== undefined && row.emp_status !== null">
              <el-dropdown trigger="click" @command="(cmd) => handleChangeEmpStatus(row, cmd)">
                <span class="status-tag-wrapper">
                  <el-tag :type="empStatusType(row.emp_status)" size="small" style="cursor: pointer">
                    {{ empStatusLabel(row.emp_status) }}
                  </el-tag>
                  <el-icon class="status-arrow"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="3" :disabled="row.emp_status === 3">在职</el-dropdown-item>
                    <el-dropdown-item :command="2" :disabled="row.emp_status === 2">试用期</el-dropdown-item>
                    <el-dropdown-item :command="1" :disabled="row.emp_status === 1">待入职</el-dropdown-item>
                    <el-dropdown-item :command="0" :disabled="row.emp_status === 0" divided>停职</el-dropdown-item>
                    <el-dropdown-item :command="-1" :disabled="row.emp_status === -1">离职</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <el-tag v-else type="info" size="small">未分配</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="账号" width="100" align="center" class-name="table-cell-flex-center-offset">
          <template #default="{ row }">
            <template v-if="row.user_id">
              <el-dropdown trigger="click" @command="(cmd) => handleChangeAccountStatus(row, cmd)">
                <span class="status-tag-wrapper">
                  <el-tag :type="accountStatusType(row.account_status)" size="small" style="cursor: pointer">
                    {{ accountStatusLabel(row.account_status) }}
                  </el-tag>
                  <el-icon class="status-arrow"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="1" :disabled="row.account_status === 1">已激活</el-dropdown-item>
                    <el-dropdown-item :command="-1" :disabled="row.account_status === -1">已禁用</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
            <el-button v-else-if="row.emp_status > 0" type="primary" size="small" link @click="handleCreateAccount(row)">
              创建账号
            </el-button>
            <el-tag v-else type="info" size="small">无账号</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center" fixed="right" class-name="table-cell-flex-center">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleEdit(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button type="success" size="small" link @click="handleManageOrg(row)">
              <el-icon><OfficeBuilding /></el-icon> 组织
            </el-button>
            <el-button type="warning" size="small" link @click="handleManageDept(row)">
              <el-icon><Folder /></el-icon> 部门
            </el-button>
            <el-button type="danger" size="small" link @click="handleDelete(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadEmployees"
          @current-change="loadEmployees"
        />
      </div>
    </el-card>
    
    <!-- 员工编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑员工' : '新建员工'" width="600px" destroy-on-close>
      <div class="section-blocks" style="gap: 0;">
        <!-- 基本信息 -->
        <div class="section-block" style="margin-bottom: 16px;">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><User /></el-icon>
              <span>基本信息</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="form" label-width="80px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="姓名" required>
                    <el-input v-model="form.name" placeholder="请输入姓名" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="员工编码">
                    <el-input v-model="form.code" placeholder="请输入员工编码" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="手机号">
                    <el-input v-model="form.mobile" placeholder="请输入手机号" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="邮箱">
                    <el-input v-model="form.email" placeholder="请输入邮箱" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="性别">
                    <el-radio-group v-model="form.gender">
                      <el-radio :label="1">男</el-radio>
                      <el-radio :label="2">女</el-radio>
                      <el-radio :label="0">未知</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </div>

        <!-- 新建员工时的附加选项 -->
        <template v-if="!form.id">
          <!-- 加入组织 -->
          <div class="section-block" style="margin-bottom: 16px;">
            <div class="section-block__header">
              <div class="section-block__title">
                <el-icon><OfficeBuilding /></el-icon>
                <span>加入组织（可选）</span>
              </div>
            </div>
            <div class="section-block__content">
              <el-form :model="form" label-width="80px">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="组织">
                      <el-select 
                        v-model="form.org_id" 
                        placeholder="选择组织" 
                        clearable 
                        @change="handleOrgSelectChange"
                        style="width: 100%"
                      >
                        <el-option v-for="org in organizations" :key="org.id" :label="org.name" :value="org.id" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="工号">
                      <el-input v-model="form.emp_no" placeholder="请输入工号" :disabled="!form.org_id" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="职位">
                      <el-input v-model="form.position" placeholder="请输入职位" :disabled="!form.org_id" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="部门">
                      <el-tree-select
                        v-model="form.dept_id"
                        :data="createDeptTree"
                        :props="{ label: 'name', value: 'id', children: 'children' }"
                        placeholder="选择部门"
                        clearable
                        check-strictly
                        :disabled="!form.org_id"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>
          </div>

          <!-- 用户账号 -->
          <div class="section-block">
            <div class="section-block__header">
              <div class="section-block__title">
                <el-icon><Key /></el-icon>
                <span>用户账号</span>
              </div>
            </div>
            <div class="section-block__content">
              <el-form :model="form" label-width="80px">
                <el-form-item>
                  <el-checkbox v-model="form.create_account">同时创建用户账号</el-checkbox>
                  <el-text type="info" size="small" style="margin-left: 8px">
                    创建后将自动分配「内部员工」角色，用户名默认使用手机号
                  </el-text>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 管理组织对话框 -->
    <el-dialog v-model="orgDialogVisible" title="管理员工组织" width="700px">
      <div v-if="currentEmployee" class="section-blocks">
        <!-- 员工信息 -->
        <div class="section-block__info">
          <div class="section-block__info-item">
            <span class="section-block__info-label">员工姓名</span>
            <span class="section-block__info-value">{{ currentEmployee.name }}</span>
          </div>
          <div class="section-block__info-item">
            <span class="section-block__info-label">手机号</span>
            <span class="section-block__info-value">{{ currentEmployee.mobile || '-' }}</span>
          </div>
        </div>

        <!-- 已加入的组织 -->
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><OfficeBuilding /></el-icon>
              <span>已加入的组织</span>
            </div>
          </div>
          <div class="section-block__table">
            <el-table :data="currentEmployee.organizations || []" size="small" max-height="200">
              <el-table-column prop="org_name" label="组织" min-width="120" />
              <el-table-column prop="emp_no" label="工号" width="100" />
              <el-table-column prop="position" label="职位" width="100" />
              <el-table-column label="主组织" width="90" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.is_primary" type="success" size="small">是</el-tag>
                  <span v-else class="text-gray">—</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" align="center">
                <template #default="{ row }">
                  <el-button
                    v-if="!row.is_primary"
                    type="primary" size="small" link
                    @click="setPrimaryOrg(row)"
                  >设为主组织</el-button>
                  <el-button type="danger" size="small" link @click="removeFromOrg(row)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="!currentEmployee.organizations?.length" class="section-block__empty">
              <el-empty description="暂未加入任何组织" :image-size="60" />
            </div>
          </div>
        </div>

        <!-- 加入新组织 -->
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Plus /></el-icon>
              <span>加入新组织</span>
            </div>
          </div>
          <div class="section-block__add">
            <el-form :inline="true" :model="addOrgForm" size="default" class="section-block__add-form">
              <el-form-item label="组织">
                <el-select v-model="addOrgForm.org_id" placeholder="选择组织" style="width: 140px">
                  <el-option v-for="org in availableOrgs" :key="org.id" :label="org.name" :value="org.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="工号">
                <el-input v-model="addOrgForm.emp_no" placeholder="工号" style="width: 100px" />
              </el-form-item>
              <el-form-item label="职位">
                <el-input v-model="addOrgForm.position" placeholder="职位" style="width: 100px" />
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="addOrgForm.set_primary">设为主组织</el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="addToOrg" :disabled="!addOrgForm.org_id">加入</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </el-dialog>
    
    <!-- 管理部门对话框 -->
    <el-dialog v-model="deptDialogVisible" title="管理员工部门" width="650px">
      <div v-if="currentEmployee" class="section-blocks">
        <!-- 员工信息 -->
        <div class="section-block__info">
          <div class="section-block__info-item">
            <span class="section-block__info-label">员工姓名</span>
            <span class="section-block__info-value">{{ currentEmployee.name }}</span>
          </div>
          <div class="section-block__info-item">
            <span class="section-block__info-label">已加入组织</span>
            <span class="section-block__info-value">{{ currentEmployee.organizations?.map(o => o.org_name).join('、') || '未分配' }}</span>
          </div>
        </div>

        <!-- 加入新部门 -->
        <div class="section-block" style="margin-bottom: 16px;">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Plus /></el-icon>
              <span>加入新部门</span>
            </div>
          </div>
          <div class="section-block__add">
            <el-alert 
              v-if="!currentEmployee.organizations?.length" 
              title="请先为该员工分配组织，才能加入部门" 
              type="warning" 
              :closable="false"
              show-icon
              style="margin-bottom: 12px;"
            />
            <el-form v-else :inline="true" :model="addDeptForm" size="default" class="section-block__add-form">
              <el-form-item label="组织">
                <el-select v-model="selectedOrgForDept" placeholder="选择组织" @change="handleOrgForDeptChange" style="width: 140px">
                  <el-option 
                    v-for="org in currentEmployee.organizations" 
                    :key="org.org_id" 
                    :label="org.org_name" 
                    :value="org.org_id" 
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="部门">
                <el-tree-select
                  v-model="addDeptForm.dept_id"
                  :data="departmentTree"
                  :props="{ label: 'name', value: 'id', children: 'children' }"
                  placeholder="选择部门"
                  check-strictly
                  :disabled="!selectedOrgForDept"
                  style="width: 180px"
                />
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="addDeptForm.set_primary">设为主部门</el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="addToDept" :disabled="!addDeptForm.dept_id">加入</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 已加入的部门 -->
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Folder /></el-icon>
              <span>已加入的部门</span>
            </div>
          </div>
          <div class="section-block__table">
            <el-table :data="currentEmployee.departments || []" size="small" max-height="200">
              <el-table-column prop="dept_name" label="部门" min-width="150" />
              <el-table-column label="主部门" width="90" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.is_primary" type="success" size="small">是</el-tag>
                  <span v-else class="text-gray">—</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" align="center">
                <template #default="{ row }">
                  <el-button
                    v-if="!row.is_primary"
                    type="primary" size="small" link
                    @click="setPrimaryDept(row)"
                  >设为主部门</el-button>
                  <el-button type="danger" size="small" link @click="removeFromDept(row)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="!currentEmployee.departments?.length" class="section-block__empty">
              <el-empty description="暂未加入任何部门" :image-size="60" />
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 账号创建结果对话框 -->
    <el-dialog
      v-model="accountResultVisible"
      title="用户账号已创建"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-alert
        :title="'账号已创建，默认密码 ' + accountResult.raw_password + '，首次登录时需强制修改密码'"
        type="success"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-descriptions :column="1" border>
        <el-descriptions-item label="员工姓名">{{ accountResult.employee_name }}</el-descriptions-item>
        <el-descriptions-item label="用户名">
          <el-tag>{{ accountResult.username }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="默认密码">
          <code>{{ accountResult.raw_password }}</code>
          <el-tag size="small" style="margin-left: 8px">首次登录需修改</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="accountResultVisible = false">知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, RefreshRight, ArrowDown, OfficeBuilding, Folder, User, Key, Edit, Delete } from '@element-plus/icons-vue'
import { employeeApi, organizationApi, departmentApi } from '../../api'

// 数据
const employees = ref([])
const organizations = ref([])
const departmentTree = ref([])
const createDeptTree = ref([])  // 创建员工时的部门树
const loading = ref(false)
const submitLoading = ref(false)

// 筛选
const filter = reactive({ org_id: null, keyword: '', emp_status: null, account_status: null })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

// 对话框
const dialogVisible = ref(false)
const orgDialogVisible = ref(false)
const deptDialogVisible = ref(false)
const currentEmployee = ref(null)

// 表单
const form = reactive({ 
  id: null, name: '', mobile: '', email: '', gender: 0,
  org_id: null, emp_no: '', position: '', dept_id: null,
  create_account: false,
})

// 账号创建结果
const accountResultVisible = ref(false)
const accountResult = reactive({ employee_name: '', username: '', raw_password: '' })
const addOrgForm = reactive({ org_id: null, emp_no: '', position: '', set_primary: false })
const addDeptForm = reactive({ dept_id: null, set_primary: false })
const selectedOrgForDept = ref(null)  // 管理部门时选择的组织

// 可选择的组织（排除已加入的）
const availableOrgs = computed(() => {
  if (!currentEmployee.value) return organizations.value
  const joinedOrgIds = (currentEmployee.value.organizations || []).map(o => o.org_id)
  return organizations.value.filter(o => !joinedOrgIds.includes(o.id))
})

// 加载员工列表
const loadEmployees = async () => {
  loading.value = true
  try {
    const params = {
      org_id: filter.org_id || undefined,
      keyword: filter.keyword || undefined,
      include: 'primary_org_name,primary_dept_name',
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filter.emp_status !== null && filter.emp_status !== '') {
      params.emp_status = filter.emp_status
    }
    if (filter.account_status !== null && filter.account_status !== '') {
      params.account_status = filter.account_status
    }
    const res = await employeeApi.list(params)
    employees.value = res.data?.rows || []
    pagination.total = res.data?.total_records || 0
  } catch (e) {
    ElMessage.error('加载员工列表失败')
  } finally {
    loading.value = false
  }
}

// 加载组织列表
const loadOrganizations = async () => {
  try {
    const res = await organizationApi.list()
    // 组织列表接口返回分页格式 { rows, total_records, page, page_size }
    organizations.value = res.data?.rows || []
  } catch (e) {
    console.error('加载组织列表失败', e)
  }
}

// 加载部门树
const loadDeptTree = async (orgId, target = 'main') => {
  // 确保 orgId 是有效的数字
  const numericOrgId = Number(orgId)
  if (!numericOrgId || isNaN(numericOrgId)) {
    if (target === 'create') createDeptTree.value = []
    else departmentTree.value = []
    return
  }
  
  try {
    const res = await departmentApi.tree(numericOrgId)
    const treeData = res.data || []
    if (target === 'create') {
      createDeptTree.value = treeData
    } else {
      departmentTree.value = treeData
    }
  } catch (e) {
    console.error('加载部门树失败:', e)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadEmployees()
}

// 重置
const handleReset = () => {
  filter.org_id = null
  filter.keyword = ''
  filter.emp_status = null
  filter.account_status = null
  pagination.page = 1
  loadEmployees()
}

// 创建员工时选择组织变化
const handleOrgSelectChange = async (orgId) => {
  form.dept_id = null
  await loadDeptTree(orgId, 'create')
}

// 创建员工
const handleCreate = () => {
  Object.assign(form, { 
    id: null, name: '', code: '', mobile: '', email: '', gender: 0,
    org_id: null, emp_no: '', position: '', dept_id: null,
    create_account: false,
  })
  createDeptTree.value = []
  dialogVisible.value = true
}

// 编辑员工
const handleEdit = (row) => {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    code: row.code || '',
    mobile: row.mobile || '',
    email: row.email || '',
    gender: row.gender || 0
  })
  dialogVisible.value = true
}

// 删除员工
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除员工「${row.name}」吗？`, '确认删除', { type: 'warning' })
    await employeeApi.delete(row.id)
    ElMessage.success('删除成功')
    loadEmployees()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '删除失败')
  }
}

// 提交表单
const submitForm = async () => {
  if (!form.name) {
    ElMessage.warning('请输入姓名')
    return
  }
  submitLoading.value = true
  try {
    if (form.id) {
      // 编辑
      await employeeApi.update(form.id, {
        name: form.name,
        code: form.code,
        mobile: form.mobile,
        email: form.email,
        gender: form.gender
      })
      ElMessage.success('更新成功')
    } else {
      // 新建
      const res = await employeeApi.create({
        name: form.name,
        code: form.code,
        mobile: form.mobile,
        email: form.email,
        gender: form.gender
      })
      const newEmpId = res.data?.id
      
      // 如果选择了组织，自动加入
      if (newEmpId && form.org_id) {
        await employeeApi.addToOrg({
          employee_id: newEmpId,
          org_id: form.org_id,
          emp_no: form.emp_no,
          position: form.position,
          set_primary: true
        })
        
        // 如果选择了部门，自动加入
        if (form.dept_id) {
          await employeeApi.addToDept({
            employee_id: newEmpId,
            dept_id: form.dept_id,
            set_primary: true
          })
        }
      }

      // 如果勾选了创建账号，自动为员工创建用户
      if (newEmpId && form.create_account) {
        try {
          const accountRes = await employeeApi.createAccount({ employee_id: newEmpId })
          const data = accountRes.data
          Object.assign(accountResult, {
            employee_name: data.employee_name,
            username: data.username,
            raw_password: data.raw_password
          })
          accountResultVisible.value = true
        } catch (accountErr) {
          // 员工已创建成功，账号创建失败不影响主流程
          ElMessage.warning('员工已创建，但用户账号创建失败：' + (accountErr.message || '未知错误'))
        }
      }
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadEmployees()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 为已有员工创建账号
const handleCreateAccount = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定为员工「${row.name}」创建用户账号吗？`,
      '创建账号',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' }
    )
    const res = await employeeApi.createAccount({ employee_id: row.id })
    const data = res.data
    Object.assign(accountResult, {
      employee_name: data.employee_name,
      username: data.username,
      raw_password: data.raw_password
    })
    accountResultVisible.value = true
    loadEmployees()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '创建账号失败')
  }
}

// 管理组织
const handleManageOrg = async (row) => {
  try {
    const res = await employeeApi.get(row.id)
    currentEmployee.value = res.data
    Object.assign(addOrgForm, { org_id: null, emp_no: '', position: '', set_primary: false })
    orgDialogVisible.value = true
  } catch (e) {
    ElMessage.error('加载员工详情失败')
  }
}

// 管理部门
const handleManageDept = async (row) => {
  try {
    // 1. 获取员工详情
    const res = await employeeApi.get(row.id)
    currentEmployee.value = res.data
    Object.assign(addDeptForm, { dept_id: null, set_primary: false })
    
    // 2. 清空部门树
    departmentTree.value = []
    selectedOrgForDept.value = null
    
    // 3. 检查员工是否有加入组织
    const orgs = res.data.organizations || []
    
    if (orgs.length > 0) {
      // 4. 选择第一个组织（优先使用主组织）
      let firstOrgId = null
      
      // 优先找主组织
      const primaryOrg = orgs.find(o => o.is_primary)
      if (primaryOrg) {
        firstOrgId = primaryOrg.org_id
      } else {
        firstOrgId = orgs[0].org_id
      }
      
      // 5. 设置选中的组织
      selectedOrgForDept.value = firstOrgId
      
      // 6. 根据选中的组织加载部门树
      if (firstOrgId) {
        await loadDeptTree(firstOrgId)
      }
    }
    
    // 7. 打开对话框
    deptDialogVisible.value = true
  } catch (e) {
    console.error('加载员工详情失败:', e)
    ElMessage.error('加载员工详情失败')
  }
}

// 切换组织时重新加载部门树
const handleOrgForDeptChange = async (orgId) => {
  console.log('切换组织:', orgId)
  addDeptForm.dept_id = null
  departmentTree.value = []
  if (orgId) {
    await loadDeptTree(orgId)
  }
}

// 加入组织
const addToOrg = async () => {
  if (!addOrgForm.org_id) {
    ElMessage.warning('请选择组织')
    return
  }
  try {
    await employeeApi.addToOrg({
      employee_id: currentEmployee.value.id,
      ...addOrgForm
    })
    ElMessage.success('加入成功')
    const res = await employeeApi.get(currentEmployee.value.id)
    currentEmployee.value = res.data
    Object.assign(addOrgForm, { org_id: null, emp_no: '', position: '', set_primary: false })
    loadEmployees()
  } catch (e) {
    ElMessage.error(e.message || '加入失败')
  }
}

// 设为主组织
const setPrimaryOrg = async (row) => {
  try {
    await employeeApi.setPrimaryOrg(currentEmployee.value.id, row.org_id)
    ElMessage.success('已设为主组织')
    const res = await employeeApi.get(currentEmployee.value.id)
    currentEmployee.value = res.data
    loadEmployees()
  } catch (e) {
    ElMessage.error(e.message || '设置失败')
  }
}

// 从组织移除
const removeFromOrg = async (row) => {
  try {
    await ElMessageBox.confirm(`确定将员工从「${row.org_name}」移除吗？`, '确认移除', { type: 'warning' })
    await employeeApi.removeFromOrg(currentEmployee.value.id, row.org_id)
    ElMessage.success('移除成功')
    const res = await employeeApi.get(currentEmployee.value.id)
    currentEmployee.value = res.data
    loadEmployees()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '移除失败')
  }
}

// 加入部门
const addToDept = async () => {
  if (!addDeptForm.dept_id) {
    ElMessage.warning('请选择部门')
    return
  }
  try {
    await employeeApi.addToDept({
      employee_id: currentEmployee.value.id,
      ...addDeptForm
    })
    ElMessage.success('加入成功')
    const res = await employeeApi.get(currentEmployee.value.id)
    currentEmployee.value = res.data
    Object.assign(addDeptForm, { dept_id: null, set_primary: false })
    loadEmployees()
  } catch (e) {
    ElMessage.error(e.message || '加入失败')
  }
}

// 设为主部门
const setPrimaryDept = async (row) => {
  try {
    await employeeApi.setPrimaryDept(currentEmployee.value.id, row.dept_id)
    ElMessage.success('已设为主部门')
    const res = await employeeApi.get(currentEmployee.value.id)
    currentEmployee.value = res.data
    loadEmployees()
  } catch (e) {
    ElMessage.error(e.message || '设置失败')
  }
}

// 从部门移除
const removeFromDept = async (row) => {
  try {
    await ElMessageBox.confirm(`确定将员工从「${row.dept_name}」部门移除吗？`, '确认移除', { type: 'warning' })
    await employeeApi.removeFromDept(currentEmployee.value.id, row.dept_id)
    ElMessage.success('移除成功')
    const res = await employeeApi.get(currentEmployee.value.id)
    currentEmployee.value = res.data
    loadEmployees()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '移除失败')
  }
}

// ==================== 状态辅助函数 ====================

const empStatusLabel = (status) => {
  const map = { '-1': '离职', 0: '停职', 1: '待入职', 2: '试用期', 3: '在职' }
  return map[status] ?? '未知'
}

const empStatusType = (status) => {
  const map = { '-1': 'info', 0: 'warning', 1: '', 2: '', 3: 'success' }
  return map[status] ?? 'info'
}

const accountStatusLabel = (status) => {
  const map = { '-1': '已禁用', 0: '未激活', 1: '已激活' }
  return map[status] ?? '未知'
}

const accountStatusType = (status) => {
  const map = { '-1': 'danger', 0: 'warning', 1: 'success' }
  return map[status] ?? 'info'
}

// 修改雇佣状态（基于主组织）
const handleChangeEmpStatus = async (row, newStatus) => {
  if (row.emp_status === newStatus) return
  const orgId = row.primary_org_id
  if (!orgId) {
    ElMessage.warning('该员工未分配主组织，无法修改雇佣状态')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定将「${row.name}」的雇佣状态改为「${empStatusLabel(newStatus)}」吗？`,
      '确认修改', { type: 'warning' }
    )
    await employeeApi.updateOrgStatus(row.id, orgId, newStatus)
    ElMessage.success('状态更新成功')
    loadEmployees()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '操作失败')
  }
}

// 修改账号状态
const handleChangeAccountStatus = async (row, newStatus) => {
  if (row.account_status === newStatus) return
  try {
    await ElMessageBox.confirm(
      `确定将「${row.name}」的账号状态改为「${accountStatusLabel(newStatus)}」吗？`,
      '确认修改', { type: 'warning' }
    )
    await employeeApi.updateAccountStatus(row.id, newStatus)
    ElMessage.success('账号状态更新成功')
    loadEmployees()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => {
  loadOrganizations()
  loadEmployees()
})
</script>

<style scoped>
@import '../../styles/components/ui/tables.css';
@import '../../styles/components/ui/filters.css';

.employee-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.employee-info span {
  font-weight: 500;
}
.avatar {
  background: linear-gradient(135deg, rgba(var(--primary), 1), rgba(var(--primary), 0.7));
}
.status-tag-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  cursor: pointer;
}
.status-arrow {
  font-size: 12px;
  color: #909399;
}
</style>
