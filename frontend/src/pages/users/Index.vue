<template>
  <div class="page-container">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" class="btn-modern" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建用户
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="用户名/姓名/邮箱">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入用户名、姓名或邮箱"
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
          <el-select
            v-model="filterForm.status"
            placeholder="请选择状态"
            clearable
          >
            <el-option label="全部" value=""></el-option>
            <el-option label="启用" value="active">
              <el-icon><Check /></el-icon> 启用
            </el-option>
            <el-option label="禁用" value="inactive">
              <el-icon><Close /></el-icon> 禁用
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="角色">
          <el-select
            v-model="filterForm.role"
            placeholder="请选择角色"
            clearable
          >
            <el-option label="全部" value=""></el-option>
            <el-option
              v-for="role in allRoles"
              :key="role.code"
              :label="role.name"
              :value="role.code"
            />
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

    <el-card class="data-card" shadow="hover">
      <el-table
        v-loading="loading"
        :data="userList"
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="id" label="ID" width="80" align="center">
          <template #default="scope">
            <el-tag type="info" size="small" effect="plain"
              >#{{ scope.row.id }}</el-tag
            >
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" min-width="120" />
        <el-table-column label="角色" min-width="150">
          <template #default="scope">
            <el-tag
              v-for="role in scope.row.roles || []"
              :key="role.code"
              size="small"
              :type="role.code === 'admin' ? 'danger' : 'primary'"
              effect="light"
              style="margin-right: 4px"
              >{{ role.name }}</el-tag
            >
            <el-text
              v-if="!(scope.row.roles || []).length"
              type="info"
              size="small"
              >无角色</el-text
            >
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag
              :type="scope.row.status === 'active' ? 'success' : 'danger'"
              size="small"
            >
              {{ scope.row.status === "active" ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="创建时间"
          width="180"
          align="center"
        >
          <template #default="scope">
            <el-text class="time-text" size="small">{{
              formatDate(scope.row.created_at)
            }}</el-text>
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="380"
          align="center"
          fixed="right"
          class-name="table-cell-flex-center"
        >
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleEdit(scope.row)"
            >
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button
              type="success"
              size="small"
              link
              @click="handleAssignRole(scope.row)"
            >
              <el-icon><Medal /></el-icon> 角色
            </el-button>
            <el-button
              type="warning"
              size="small"
              link
              @click="handleAssignSSORole(scope.row)"
            >
              <el-icon><Connection /></el-icon> SSO
            </el-button>
            <el-button
              :type="scope.row.status === 'active' ? 'danger' : 'success'"
              size="small"
              link
              @click="handleToggleStatus(scope.row)"
            >
              <el-icon
                ><component :is="scope.row.status === 'active' ? Lock : Unlock"
              /></el-icon>
              {{ scope.row.status === "active" ? "禁用" : "启用" }}
            </el-button>
            <el-button
              type="primary"
              size="small"
              link
              @click="handleResetPassword(scope.row)"
            >
              <el-icon><Key /></el-icon> 重置密码
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <EmptyState
        v-if="!loading && userList.length === 0"
        type="data"
        :icon="Collection"
        title="暂无用户"
        :description="
          searchKeyword || filterForm.status || filterForm.role
            ? '没有找到符合条件的用户，请调整搜索条件'
            : '还没有创建任何用户，点击下方按钮创建第一个用户'
        "
        :action-text="
          searchKeyword || filterForm.status || filterForm.role
            ? '重置筛选'
            : '新建用户'
        "
        :action-icon="
          searchKeyword || filterForm.status || filterForm.role
            ? RefreshRight
            : Plus
        "
        @action="
          searchKeyword || filterForm.status || filterForm.role
            ? handleReset()
            : handleCreate()
        "
      />

      <div class="pagination-container" v-if="userList.length > 0">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        ></el-pagination>
      </div>
    </el-card>

    <!-- 新建用户对话框 -->
    <UserCreateDialog
      v-model="createDialogVisible"
      @success="handleCreateSuccess"
    />

    <!-- 编辑用户对话框 -->
    <UserEditDialog
      v-model="editDialogVisible"
      :user="currentEditUser"
      @success="handleEditSuccess"
    />

    <!-- 角色分配对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="`分配角色 - ${roleDialogUser?.username || ''}`"
      width="500px"
      align-center
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Medal /></el-icon>
              <span>选择角色</span>
            </div>
          </div>
          <div class="section-block__content" v-loading="roleDialogLoading">
            <p
              style="
                margin-bottom: 16px;
                color: var(--el-text-color-secondary);
                font-size: var(--el-font-size-sm);
              "
            >
              勾选要分配给该用户的角色：
            </p>
            <el-checkbox-group v-model="selectedRoleCodes">
              <el-checkbox
                v-for="role in allRoles"
                :key="role.code"
                :label="role.code"
                :value="role.code"
                style="display: block; margin-bottom: 12px"
              >
                <span style="font-weight: var(--el-font-weight-bold)">{{
                  role.name
                }}</span>
                <span
                  style="
                    color: var(--el-text-color-secondary);
                    margin-left: 8px;
                    font-size: var(--el-font-size-xs);
                  "
                >
                  {{ role.code }}
                </span>
                <span
                  v-if="role.description"
                  style="
                    color: var(--el-text-color-placeholder);
                    margin-left: 8px;
                    font-size: var(--el-font-size-xs);
                  "
                >
                  - {{ role.description }}
                </span>
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="roleDialogSaving"
          @click="handleSaveRoles"
          >保存</el-button
        >
      </template>
    </el-dialog>

    <!-- SSO 角色分配对话框 -->
    <el-dialog
      v-model="ssoRoleDialogVisible"
      :title="`分配 SSO 角色 - ${ssoRoleDialogUser?.username || ''}`"
      width="500px"
      align-center
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Connection /></el-icon>
              <span>选择 SSO 角色</span>
            </div>
          </div>
          <div class="section-block__content" v-loading="ssoRoleDialogLoading">
            <p
              style="
                margin-bottom: 16px;
                color: var(--el-text-color-secondary);
                font-size: var(--el-font-size-sm);
              "
            >
              勾选要分配给该用户的 SSO 角色（用于同步给外部系统）：
            </p>
            <el-checkbox-group v-model="selectedSSORoleCodes">
              <el-checkbox
                v-for="role in allSSORoles"
                :key="role.code"
                :label="role.code"
                :value="role.code"
                :disabled="!role.is_active"
                style="display: block; margin-bottom: 12px"
              >
                <span style="font-weight: var(--el-font-weight-bold)">{{
                  role.name
                }}</span>
                <span
                  style="
                    color: var(--el-text-color-secondary);
                    margin-left: 8px;
                    font-size: var(--el-font-size-xs);
                  "
                >
                  {{ role.code }}
                </span>
                <el-tag
                  v-if="!role.is_active"
                  type="info"
                  size="small"
                  style="margin-left: 8px"
                  >已禁用</el-tag
                >
                <span
                  v-if="role.description"
                  style="
                    color: var(--el-text-color-placeholder);
                    margin-left: 8px;
                    font-size: var(--el-font-size-xs);
                  "
                >
                  - {{ role.description }}
                </span>
              </el-checkbox>
            </el-checkbox-group>
            <div v-if="allSSORoles.length === 0" class="section-block__empty">
              <el-empty :image-size="60">
                <template #description>
                  <div
                    style="
                      text-align: center;
                      align-items: center;
                      display: flex;
                    "
                  >
                    暂无 SSO 角色 请先在
                    <el-link type="primary" @click="goToSSORoles"
                      >SSO 角色管理</el-link
                    >
                    中创建
                  </div>
                </template>
              </el-empty>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="ssoRoleDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="ssoRoleDialogSaving"
          @click="handleSaveSSORoles"
          >保存</el-button
        >
      </template>
    </el-dialog>

    <!-- 重置密码确认对话框 -->
    <el-dialog
      v-model="resetPasswordVisible"
      title="重置密码"
      width="400px"
      align-center
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0">
        <div class="section-block">
          <div class="section-block__content" style="padding: 16px">
            <p
              style="
                margin: 0;
                color: var(--el-text-color-regular);
                font-size: var(--el-font-size-base);
                line-height: var(--c-line-height-md);
              "
            >
              确定要重置用户
              <strong>{{ resetPasswordUser?.username }}</strong> 的密码吗？
            </p>
            <p
              style="
                margin: 8px 0 0 0;
                color: var(--el-text-color-secondary);
                font-size: var(--el-font-size-sm);
                line-height: var(--c-line-height-sm);
              "
            >
              重置后将生成临时密码，用户首次登录时需强制修改密码。
            </p>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resetPasswordVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleResetPasswordSubmit"
            :loading="resetPasswordLoading"
            >确定重置</el-button
          >
        </div>
      </template>
    </el-dialog>

    <!-- 重置密码结果对话框 -->
    <el-dialog
      v-model="resetPasswordResultVisible"
      title="密码已重置"
      width="480px"
      align-center
      :close-on-click-modal="false"
    >
      <div class="section-blocks" style="gap: 0">
        <div class="section-block">
          <div class="section-block__content" style="padding: 16px">
            <el-alert
              title="密码重置成功，请妥善保存以下临时密码"
              type="success"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            />
            <el-descriptions :column="1" border>
              <el-descriptions-item label="用户名">{{
                resetPasswordUser?.username
              }}</el-descriptions-item>
              <el-descriptions-item label="临时密码">
                <code
                  style="
                    font-size: var(--el-font-size-md);
                    font-weight: var(--el-font-weight-extra-bold);
                    color: var(--el-color-danger);
                  "
                  >{{ resetPasswordResult?.password }}</code
                >
              </el-descriptions-item>
            </el-descriptions>
            <p
              style="
                margin: 16px 0 0 0;
                color: var(--el-text-color-secondary);
                font-size: var(--el-font-size-sm);
              "
            >
              <el-icon style="vertical-align: middle; margin-right: 4px"
                ><Warning
              /></el-icon>
              用户首次登录时需强制修改密码
            </p>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="handleCopyPassword"
          >复制密码</el-button
        >
        <el-button @click="resetPasswordResultVisible = false"
          >知道了</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Search,
  RefreshRight,
  Edit,
  Key,
  Unlock,
  Lock,
  Check,
  Close,
  UserFilled,
  Connection,
  Medal,
  Warning,
  Collection,
} from "@element-plus/icons-vue";
import { userApi, roleApi, ssoRoleApi } from "@/api";
import { handleApiError, getDefaultErrorMessage } from "@/utils/errorHandler";
import UserCreateDialog from "./Create.vue";
import UserEditDialog from "./Edit.vue";
import EmptyState from "@/components/EmptyState.vue";

const router = useRouter();

// 表格数据
const userList = ref([]);
const loading = ref(false);
const searchKeyword = ref("");

// 筛选表单
const filterForm = reactive({});

// 分页数据
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0,
});

// 对话框状态
const createDialogVisible = ref(false);
const editDialogVisible = ref(false);
const currentEditUser = ref(null);

// 重置密码对话框数据
const resetPasswordVisible = ref(false);
const resetPasswordLoading = ref(false);
const resetPasswordUser = ref(null);
const resetPasswordResultVisible = ref(false);
const resetPasswordResult = ref(null);

// ==================== 角色分配 ====================

const roleDialogVisible = ref(false);
const roleDialogLoading = ref(false);
const roleDialogSaving = ref(false);
const roleDialogUser = ref(null);
const allRoles = ref([]);
const selectedRoleCodes = ref([]);
const originalRoleCodes = ref([]);

// 获取全部角色列表（缓存，页面加载时获取一次）
const fetchAllRoles = async () => {
  try {
    const response = await roleApi.list();
    allRoles.value = response.data || [];
  } catch (error) {
    // 错误已在API拦截器中处理
    allRoles.value = [];
  }
};

// 打开角色分配对话框
const handleAssignRole = (row) => {
  roleDialogUser.value = row;
  roleDialogVisible.value = true;
  // 直接从列表数据中获取角色，无需额外请求
  const userRoles = row.roles || [];
  selectedRoleCodes.value = userRoles.map((r) => r.code);
  originalRoleCodes.value = [...selectedRoleCodes.value];
};

// 保存角色分配（对比差异，增量操作）
const handleSaveRoles = async () => {
  const toAdd = selectedRoleCodes.value.filter(
    (c) => !originalRoleCodes.value.includes(c),
  );
  const toRemove = originalRoleCodes.value.filter(
    (c) => !selectedRoleCodes.value.includes(c),
  );

  if (toAdd.length === 0 && toRemove.length === 0) {
    roleDialogVisible.value = false;
    return;
  }

  roleDialogSaving.value = true;
  try {
    const userId = roleDialogUser.value.id;
    // 依次执行添加和移除
    for (const code of toAdd) {
      await roleApi.assignRole({ user_id: userId, role_code: code });
    }
    for (const code of toRemove) {
      await roleApi.unassignRole({ user_id: userId, role_code: code });
    }
    ElMessage.success("角色分配已更新");
    roleDialogVisible.value = false;
    getUsersList(); // 刷新列表
  } catch (error) {
    handleApiError(error, "角色分配失败");
  } finally {
    roleDialogSaving.value = false;
  }
};

// ==================== SSO 角色分配 ====================

const ssoRoleDialogVisible = ref(false);
const ssoRoleDialogLoading = ref(false);
const ssoRoleDialogSaving = ref(false);
const ssoRoleDialogUser = ref(null);
const allSSORoles = ref([]);
const selectedSSORoleCodes = ref([]);

// 获取全部 SSO 角色列表
const fetchAllSSORoles = async () => {
  try {
    const response = await ssoRoleApi.list();
    allSSORoles.value = response.data || [];
  } catch (error) {
    // 错误已在API拦截器中处理
    allSSORoles.value = [];
  }
};

// 打开 SSO 角色分配对话框
const handleAssignSSORole = async (row) => {
  ssoRoleDialogUser.value = row;
  ssoRoleDialogVisible.value = true;
  ssoRoleDialogLoading.value = true;
  try {
    // 获取该用户当前的 SSO 角色
    const response = await ssoRoleApi.getUserRoles(row.id);
    const userRoles = response.data || [];
    selectedSSORoleCodes.value = userRoles.map((r) => r.code);
  } catch (error) {
    handleApiError(error, "获取用户 SSO 角色失败");
    selectedSSORoleCodes.value = [];
  } finally {
    ssoRoleDialogLoading.value = false;
  }
};

// 保存 SSO 角色分配（全量设置）
const handleSaveSSORoles = async () => {
  ssoRoleDialogSaving.value = true;
  try {
    await ssoRoleApi.setUserRoles({
      user_id: ssoRoleDialogUser.value.id,
      sso_role_codes: selectedSSORoleCodes.value,
    });
    ElMessage.success("SSO 角色分配已更新");
    ssoRoleDialogVisible.value = false;
  } catch (error) {
    handleApiError(error, "SSO 角色分配失败");
  } finally {
    ssoRoleDialogSaving.value = false;
  }
};

// 跳转到 SSO 角色管理页面
const goToSSORoles = () => {
  ssoRoleDialogVisible.value = false;
  router.push("/sso-roles");
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return "-";
  const date = new Date(dateString);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

// 获取用户列表
const getUsersList = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      keyword: searchKeyword.value || undefined,
    };

    // 添加状态筛选参数
    if (filterForm.status !== undefined && filterForm.status !== "") {
      params.status = filterForm.status;
    }

    // 添加角色筛选参数
    if (filterForm.role !== undefined && filterForm.role !== "") {
      params.role = filterForm.role;
    }

    const response = await userApi.list(params);
    // 后端返回统一的 PageResponse 格式: { message, data: { rows, total_records, page, page_size } }
    const data = response.data || {};
    const rows = data.rows || [];
    pagination.total = data.total_records || 0;

    // 后端已通过 selectinload 预加载角色，每条 row 自带 roles: [{code, name}, ...]
    userList.value = rows;
  } catch (error) {
    handleApiError(error, getDefaultErrorMessage("get"));
    userList.value = [];
    pagination.total = 0;
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  pagination.currentPage = 1;
  getUsersList();
};

// 重置筛选条件
const handleReset = () => {
  searchKeyword.value = "";
  filterForm.status = "";
  filterForm.role = "";
  pagination.currentPage = 1;
  getUsersList();
};

// 分页大小改变
const handleSizeChange = (val) => {
  pagination.pageSize = val;
  pagination.currentPage = 1;
  getUsersList();
};

// 当前页改变
const handleCurrentChange = (val) => {
  pagination.currentPage = val;
  getUsersList();
};

// 新建用户
const handleCreate = () => {
  createDialogVisible.value = true;
};

// 编辑用户
const handleEdit = (row) => {
  currentEditUser.value = row;
  editDialogVisible.value = true;
};

// 切换用户状态
const handleToggleStatus = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.status === "active" ? "禁用" : "启用"}用户 "${row.name}" 吗？`,
      "提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const action = row.status === "active" ? "disable" : "enable";
    await userApi[action](row.id);

    ElMessage.success(`用户${row.status === "active" ? "禁用" : "启用"}成功`);
    getUsersList();
  } catch (error) {
    if (error !== "cancel") {
      handleApiError(error, getDefaultErrorMessage("update"));
    }
  }
};

// 重置密码
const handleResetPassword = (row) => {
  resetPasswordUser.value = row;
  resetPasswordVisible.value = true;
};

// 提交重置密码
const handleResetPasswordSubmit = async () => {
  if (!resetPasswordUser.value) return;

  try {
    resetPasswordLoading.value = true;

    const response = await userApi.resetPassword(resetPasswordUser.value.id);
    resetPasswordResult.value = response.data;

    resetPasswordVisible.value = false;
    resetPasswordResultVisible.value = true;
    ElMessage.success("密码重置成功");
  } catch (error) {
    handleApiError(error, getDefaultErrorMessage("update"));
  } finally {
    resetPasswordLoading.value = false;
  }
};

// 复制密码到剪贴板
const handleCopyPassword = () => {
  if (!resetPasswordResult.value?.password) return;

  navigator.clipboard
    .writeText(resetPasswordResult.value.password)
    .then(() => {
      ElMessage.success("密码已复制到剪贴板");
    })
    .catch(() => {
      ElMessage.error("复制失败，请手动复制");
    });
};

// 新建成功回调
const handleCreateSuccess = () => {
  createDialogVisible.value = false;
  getUsersList();
};

// 编辑成功回调
const handleEditSuccess = () => {
  editDialogVisible.value = false;
  getUsersList();
};

// 初始化
onMounted(() => {
  fetchAllRoles();
  fetchAllSSORoles();
  getUsersList();
});
</script>
<style scoped></style>
