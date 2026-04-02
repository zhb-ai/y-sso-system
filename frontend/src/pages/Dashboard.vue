<template>
  <div class="page-container">
    <div class="page-header">
      <h2>仪表盘</h2>
      <h5>欢迎回来，{{ userInfo?.username || '管理员' }}！</h5>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <template v-if="loading">
        <el-card shadow="hover" class="stat-card" v-for="i in 4" :key="i">
          <div class="stat-content">
            <div class="stat-info">
              <el-skeleton animated :rows="1" />
              <el-skeleton animated :rows="1" />
            </div>
            <div class="stat-icon skeleton-icon">
              <el-skeleton animated :rows="1" />
            </div>
          </div>
        </el-card>
      </template>
      <template v-else>
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <h3>{{ applicationCount }}</h3>
              <p>已注册应用</p>
            </div>
            <div class="stat-icon application">
              <el-icon><Grid /></el-icon>
            </div>
          </div>
        </el-card>
        
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <h3>{{ userCount }}</h3>
              <p>日活用户</p>
            </div>
            <div class="stat-icon user">
              <el-icon><User /></el-icon>
            </div>
          </div>
        </el-card>
        
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <h3>{{ employeeCount }}</h3>
              <p>员工数量</p>
            </div>
            <div class="stat-icon role">
              <el-icon><Management /></el-icon>
            </div>
          </div>
        </el-card>
        
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <h3>{{ departmentCount }}</h3>
              <p>部门数量</p>
            </div>
            <div class="stat-icon department">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
          </div>
        </el-card>
      </template>
    </div>
    
    <!-- 最近登录记录筛选条件 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" :model="loginFilterForm" class="filter-form">
        <el-form-item label="用户名">
          <el-input
            v-model="searchUsername"
            placeholder="请输入用户名"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="登录IP">
          <el-input
            v-model="searchIp"
            placeholder="请输入登录IP"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Monitor /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="loginFilterForm.status" placeholder="请选择状态" clearable>
            <el-option label="全部" value=""></el-option>
            <el-option label="成功" value="success">
              <el-icon><Check /></el-icon> 成功
            </el-option>
            <el-option label="失败" value="failed">
              <el-icon><Close /></el-icon> 失败
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

    <!-- 登录记录 -->
    <el-card class="data-card login-record-card" shadow="hover">
      <template #header>
        <div class="login-record-header">
          <div class="header-title">
            <el-icon class="title-icon"><Clock /></el-icon>
            <span class="title-text">登录记录</span>
          </div>
          <el-tag type="info" size="small" v-if="recentLogins.length > 0" class="count-tag">
            共 {{ pagination.total }} 条
          </el-tag>
        </div>
      </template>

      <!-- 空状态 -->
      <EmptyState
        v-if="!loginLoading && recentLogins.length === 0"
        type="data"
        :icon="Clock"
        title="暂无登录记录"
        description="系统还没有记录任何登录行为，当有用户登录后，这里将显示最近的登录活动"
        compact
      />

      <el-table
        v-else
        v-loading="loginLoading"
        :data="recentLogins"
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" width="90" />
        <el-table-column prop="ip_address" label="登录IP" width="120" />
        <el-table-column prop="user_agent" label="浏览器信息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="登录时间" width="160">
          <template #default="scope">
            <el-text class="time-text" size="small">{{ formatDate(scope.row.created_at) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="70" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ scope.row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="failure_reason" label="失败原因" width="120" show-overflow-tooltip>
          <template #default="scope">
            <span v-if="scope.row.failure_reason" class="failure-reason">{{ scope.row.failure_reason }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          popper-class="pagination-select-dropdown"
        ></el-pagination>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { dashboardApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { Grid, User, Management, OfficeBuilding, Monitor, Search, RefreshRight, Check, Close, Clock } from '@element-plus/icons-vue'
import EmptyState from '@/components/EmptyState.vue'

const authStore = useAuthStore()
const userInfo = computed(() => authStore.userInfo)

// 加载状态
const loading = ref(true)
const loginLoading = ref(true)

// 统计数据
const applicationCount = ref(0)
const userCount = ref(0)
const departmentCount = ref(0)
const employeeCount = ref(0)

// 最近登录记录分页
const recentLogins = ref([])
const pagination = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 登录记录搜索表单
const loginFilterForm = reactive({
  status: ''
})
const searchUsername = ref('')
const searchIp = ref('')

// 获取统计数据
const fetchStatistics = async () => {
  loading.value = true
  try {
    // BaseResponse 格式: { message, msg_details, data }
    const response = await dashboardApi.getStatistics()
    // 直接从 response.data 获取数据
    const data = response.data || {}
    applicationCount.value = data.application_count || 0
    userCount.value = data.user_count || 0
    departmentCount.value = data.department_count || 0
    employeeCount.value = data.employee_count || 0
  } catch (error) {
    // 错误已在API拦截器中处理
  } finally {
    loading.value = false
  }
}

// 获取最近登录记录
const fetchRecentLogins = async (page = 1) => {
  loginLoading.value = true
  try {
    const params = {
      page: page,
      page_size: pagination.value.pageSize
    }
    
    // 添加搜索参数
    if (searchUsername.value) {
      params.username = searchUsername.value
    }
    if (searchIp.value) {
      params.ip_address = searchIp.value  // Note: backend uses ip_address, not ip
    }
    if (loginFilterForm.status) {
      params.status = loginFilterForm.status
    }
    
    // BaseResponse 格式: { message, msg_details, data }
    // data 为分页对象: { rows, total_records, page, page_size, total_pages, has_prev, has_next }
    const response = await dashboardApi.getRecentLogins(params)
    
    const data = response.data || {}
    // 分页数据格式
    if (data.rows) {
      recentLogins.value = data.rows
      pagination.value.total = data.total_records || 0
      pagination.value.currentPage = data.page || page
    } else if (Array.isArray(data)) {
      // 兼容直接返回数组的情况
      recentLogins.value = data
      pagination.value.total = data.length
      pagination.value.currentPage = page
    } else {
      recentLogins.value = []
      pagination.value.total = 0
    }
  } catch (error) {
    // 错误已在API拦截器中处理
    // 出错时显示空数组
    recentLogins.value = []
    pagination.value.total = 0
  } finally {
    loginLoading.value = false
  }
}

// 分页相关方法
const handleSizeChange = (size) => {
  pagination.value.pageSize = size
  fetchRecentLogins(pagination.value.currentPage)
}

const handleCurrentChange = (page) => {
  fetchRecentLogins(page)
}

// 搜索相关方法
const handleSearch = async () => {
  pagination.value.currentPage = 1
  await fetchRecentLogins(1)
}

const handleReset = () => {
  searchUsername.value = ''
  searchIp.value = ''
  loginFilterForm.status = ''
  pagination.value.currentPage = 1
  fetchRecentLogins(1)
}

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

onMounted(() => {
  // 从API获取真实数据
  fetchStatistics()
  fetchRecentLogins()
})
</script>

<style scoped>

.failure-reason {
  color: var(--el-color-danger);
  font-size: var(--el-font-size-xs);
}

/* 骨架屏样式 */
.skeleton-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: var(--el-color-bg-secondary);
}

/* 统计卡片布局 */
.stat-info h3 {
  min-height: 24px;
}

.stat-info p {
  min-height: 16px;
}

/* 登录记录卡片 - 扁平化标题设计 */
.login-record-card :deep(.el-card__header) {
  background-color: transparent;
  border-bottom: 1px solid var(--el-border-color-lighter);
  border-radius: 0;
  padding: 16px 20px;
}

.login-record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: var(--el-font-size-lg);
  color: var(--el-color-primary);
}

.title-text {
  font-size: var(--el-font-size-lg);
  font-weight: var(--el-font-weight-bold);
  color: var(--el-text-color-primary);
}

.count-tag {
  font-size: var(--el-font-size-xs);
}
</style>