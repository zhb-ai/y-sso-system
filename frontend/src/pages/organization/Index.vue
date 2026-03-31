<template>
  <div class="page-container">
    <div class="page-header">
      <h2>组织架构</h2>
      <div class="header-actions">
        <el-button type="success" class="btn-modern" @click="handleCreateEmployee">
          <el-icon><User /></el-icon> 新建员工
        </el-button>
        <el-button type="primary" class="btn-modern" @click="handleCreateOrg">
          <el-icon><Plus /></el-icon> 新建组织
        </el-button>
      </div>
    </div>
    
    <!-- 组织选择 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="当前组织">
          <el-select v-model="currentOrgId" placeholder="请选择组织" @change="handleOrgChange">
            <el-option v-for="org in organizations" :key="org.id" :label="org.name" :value="org.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="currentOrg">
          <el-tag class="org-code-tag" type="info">编码: {{ currentOrg.code }}</el-tag>
        </el-form-item>
        <!-- 企业微信绑定状态 -->
        <el-form-item v-if="currentOrg">
        <el-button type="warning" class="btn-modern" @click="handleEditOrg" v-if="currentOrg">
            <el-icon><Edit /></el-icon> 编辑组织
          </el-button>
          <el-tooltip content="同步通讯录功能，需要绑定企业微信，才能使用" :disabled="wechatBound">
            <el-button
              type="primary"
              class="btn-modern"
              :disabled="!wechatBound"
              @click="handleWechatSync"
              :loading="wechatSyncLoading"
            >
              同步通讯录
            </el-button>
          </el-tooltip>
          <template v-if="wechatBound">
            <el-tag type="success" style="margin-right: 8px">已绑定企业微信</el-tag>
            <el-button type="info" class="btn-modern" @click="showWechatConfigDialog">
              查看配置
            </el-button>
            <el-tooltip content="解除组织与企业微信的绑定，不再接收通讯录变更通知，已同步的数据会保留">
              <el-button type="danger" class="btn-modern" plain @click="handleWechatUnbind">
                解绑
              </el-button>
            </el-tooltip>
          </template>
          <template v-else>
            <el-button type="success" class="btn-modern" @click="showWechatBindDialog">
              绑定企业微信
            </el-button>
          </template>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 主内容区：左右布局 -->
    <div class="main-content-row" v-if="currentOrgId">
      <!-- 左侧：部门树 -->
      <el-card class="department-card" shadow="hover">
        <div class="dept-card-header">
          <h3>部门结构</h3>
          <el-button type="primary" size="small" @click="handleCreateDept(null)">
            <el-icon><Plus /></el-icon> 添加部门
          </el-button>
        </div>
        
        <el-tree
          ref="deptTreeRef"
          v-loading="deptLoading"
          :data="departmentTree"
          node-key="id"
          default-expand-all
          highlight-current
          :props="{ label: 'name', children: 'children' }"
          @node-click="handleDeptClick"
        >
          <template #default="{ node, data }">
            <div class="tree-node-content">
              <el-icon class="dept-icon"><Folder /></el-icon>
              <span class="dept-name">{{ node.label }}</span>
              <el-tag size="small" type="info" class="dept-count">{{ data.employee_count || 0 }}</el-tag>
              <span class="dept-actions">
                <el-tooltip content="添加子部门">
                  <el-button type="primary" size="small" link @click.stop="handleCreateDept(data)">
                    <el-icon><Plus /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="编辑部门">
                  <el-button type="warning" size="small" link @click.stop="handleEditDept(data)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="删除部门">
                  <el-button type="danger" size="small" link @click.stop="handleDeleteDept(data)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </span>
            </div>
          </template>
        </el-tree>
        
        <EmptyState
          v-if="!deptLoading && departmentTree.length === 0"
          type="data"
          :icon="Folder"
          title="暂无部门"
          description="当前组织下还没有创建任何部门，点击下方按钮创建第一个部门"
          action-text="添加部门"
          :action-icon="Plus"
          compact
          @action="handleCreateDept(null)"
        />
      </el-card>
      
      <!-- 右侧：员工列表 -->
      <el-card class="data-card employee-list-card" shadow="hover">
        <div class="list-header">
          <h4>
            <template v-if="selectedDept">{{ selectedDept.name }} - 员工</template>
            <template v-else>请选择部门查看员工</template>
          </h4>
          <el-button
            type="primary"
            size="small"
            @click="handleAddEmployeeToDept"
            :disabled="!selectedDept"
          >
            <el-icon><UserFilled /></el-icon> 添加员工到部门
          </el-button>
        </div>

        <!-- 筛选条件 -->
        <div v-if="selectedDept" class="list-filter">
          <el-form :inline="true" class="filter-form">
            <el-form-item label="雇佣状态">
              <el-select v-model="empStatusFilter" placeholder="全部" clearable @change="loadDeptEmployees" style="width: 110px">
                <el-option label="在职" :value="3" />
                <el-option label="试用期" :value="2" />
                <el-option label="待入职" :value="1" />
                <el-option label="停职" :value="0" />
                <el-option label="离职" :value="-1" />
              </el-select>
            </el-form-item>
            <el-form-item label="账号状态">
              <el-select v-model="accountStatusFilter" placeholder="全部" clearable @change="loadDeptEmployees" style="width: 110px">
                <el-option label="已激活" :value="1" />
                <el-option label="未激活" :value="0" />
                <el-option label="已禁用" :value="-1" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <el-table
          v-if="selectedDept"
          v-loading="employeeLoading"
          :data="deptEmployees"
          style="width: 100%"
          row-key="id"
        >
          <el-table-column prop="name" label="姓名" min-width="80">
            <template #default="{ row }">
              <div class="employee-name">
                <el-avatar :size="24">{{ row.name?.charAt(0) }}</el-avatar>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="emp_no" label="工号" width="100" />
          <el-table-column prop="position" label="职位" min-width="100" />
          <el-table-column prop="mobile" label="手机" min-width="120" />
          <el-table-column label="雇佣状态" width="100" align="center" class-name="table-cell-flex-center-offset">
            <template #default="{ row }">
              <el-dropdown trigger="click" @command="(cmd) => handleChangeEmpStatus(row, cmd)">
                <span class="status-tag-wrapper">
                  <el-tag :type="empStatusType(row.status)" size="small" style="cursor: pointer">
                    {{ empStatusLabel(row.status) }}
                  </el-tag>
                  <el-icon class="status-arrow"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="3" :disabled="row.status === 3">在职</el-dropdown-item>
                    <el-dropdown-item :command="2" :disabled="row.status === 2">试用期</el-dropdown-item>
                    <el-dropdown-item :command="1" :disabled="row.status === 1">待入职</el-dropdown-item>
                    <el-dropdown-item :command="0" :disabled="row.status === 0" divided>停职</el-dropdown-item>
                    <el-dropdown-item :command="-1" :disabled="row.status === -1">离职</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
          <el-table-column label="账号" width="90" align="center" class-name="table-cell-flex-center-offset">
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
              <el-tag v-else type="info" size="small">无账号</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" align="center" class-name="table-cell-flex-center">
            <template #default="{ row }">
              <el-button type="primary" size="small" link @click="handleEditEmployee(row)">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button type="danger" size="small" link @click="handleRemoveFromDept(row)">
                <el-icon><Remove /></el-icon> 移出
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <EmptyState
          v-else
          type="data"
          :icon="Collection"
          title="请选择部门"
          description="点击左侧部门树中的部门，查看该部门下的员工列表"
          compact
        />
        
        <div class="pagination-container" v-if="selectedDept && employeePagination.total > 0">
          <el-pagination
            v-model:current-page="employeePagination.page"
            v-model:page-size="employeePagination.pageSize"
            :total="employeePagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadDeptEmployees"
            @size-change="loadDeptEmployees"
          />
        </div>
      </el-card>
    </div>
    
    <!-- 组织编辑对话框 -->
    <el-dialog v-model="orgDialogVisible" :title="orgForm.id ? '编辑组织' : '新建组织'" width="500px" destroy-on-close>
      <div class="section-blocks" style="gap: 0;">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><OfficeBuilding /></el-icon>
              <span>基本信息</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="orgForm" label-width="80px">
              <el-form-item label="名称" required>
                <el-input v-model="orgForm.name" placeholder="请输入组织名称" autocomplete="off" />
              </el-form-item>
              <el-form-item label="编码" required>
                <el-input v-model="orgForm.code" placeholder="请输入组织编码" autocomplete="off" />
              </el-form-item>
              <el-form-item label="备注">
                <el-input v-model="orgForm.note" type="textarea" :rows="3" placeholder="请输入备注" autocomplete="off" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="orgDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitOrgForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 部门编辑对话框 -->
    <el-dialog v-model="deptDialogVisible" :title="deptForm.id ? '编辑部门' : '新建部门'" width="500px" destroy-on-close>
      <div class="section-blocks" style="gap: 0;">
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Folder /></el-icon>
              <span>基本信息</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="deptForm" label-width="80px">
              <el-form-item label="名称" required>
                <el-input v-model="deptForm.name" placeholder="请输入部门名称" autocomplete="off" />
              </el-form-item>
              <el-form-item label="父部门">
                <el-tree-select
                  v-model="deptForm.parent_id"
                  :data="departmentTree"
                  :props="{ label: 'name', value: 'id', children: 'children' }"
                  placeholder="选择父部门（留空为根部门）"
                  clearable
                  check-strictly
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="排序">
                <el-input-number v-model="deptForm.sort_order" :min="0" style="width: 120px" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="deptDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDeptForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 员工编辑对话框 -->
    <el-dialog
      v-model="employeeDialogVisible"
      :title="employeeForm.id ? '编辑员工' : '新建员工'"
      width="650px"
      destroy-on-close
    >
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
            <el-form :model="employeeForm" label-width="80px">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="姓名" required>
                    <el-input v-model="employeeForm.name" placeholder="请输入姓名" autocomplete="off" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="手机">
                    <el-input v-model="employeeForm.mobile" placeholder="请输入手机号" autocomplete="off" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="邮箱">
                    <el-input v-model="employeeForm.email" placeholder="请输入邮箱" autocomplete="off" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="性别">
                    <el-radio-group v-model="employeeForm.gender">
                      <el-radio :label="0">未知</el-radio>
                      <el-radio :label="1">男</el-radio>
                      <el-radio :label="2">女</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </div>

        <!-- 新建员工时显示加入组织选项 -->
        <template v-if="!employeeForm.id">
          <div class="section-block">
            <div class="section-block__header">
              <div class="section-block__title">
                <el-icon><OfficeBuilding /></el-icon>
                <span>加入组织</span>
              </div>
            </div>
            <div class="section-block__content">
              <el-form :model="employeeForm" label-width="80px">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="工号">
                      <el-input v-model="employeeForm.emp_no" placeholder="请输入工号" autocomplete="off" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="职位">
                      <el-input v-model="employeeForm.position" placeholder="请输入职位" autocomplete="off" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item label="加入部门">
                  <el-tree-select
                    v-model="employeeForm.dept_id"
                    :data="departmentTree"
                    :props="{ label: 'name', value: 'id', children: 'children' }"
                    placeholder="选择要加入的部门（可选）"
                    clearable
                    check-strictly
                    style="width: 100%"
                  />
                </el-form-item>
              </el-form>
            </div>
          </div>
        </template>
      </div>
      <template #footer>
        <el-button @click="employeeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEmployeeForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 添加员工到部门对话框 -->
    <el-dialog 
      v-model="addToDeptDialogVisible" 
      title="添加员工到部门" 
      width="700px"
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0;">
        <!-- 部门信息 -->
        <div class="section-block" style="margin-bottom: 16px;">
          <div class="section-block__content" style="padding: 12px 16px;">
            <div class="dept-tips">
              <el-icon style="color: var(--el-color-info); font-size: var(--el-font-size-md);"><Info-Filled /></el-icon>
              <div class="dept-tips__content">
                <div class="dept-tips__title">将员工添加到「{{ selectedDept?.name }}」部门</div>
                <div class="dept-tips__desc">搜索系统中的员工，如果员工尚未加入当前组织，将自动添加</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 搜索员工 -->
        <div class="section-block" style="margin-bottom: 16px;">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Search /></el-icon>
              <span>搜索员工</span>
            </div>
            <div class="section-block__actions">
              <el-button type="success" size="small" @click="handleCreateAndAddEmployee">
                <el-icon><Plus /></el-icon> 新建并添加
              </el-button>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :inline="true" class="section-block__add-form">
              <el-form-item label="关键词">
                <el-input 
                  v-model="searchKeyword" 
                  placeholder="输入姓名或手机号" 
                  clearable
                  autocomplete="off"
                  @keyup.enter="searchEmployees"
                  style="width: 200px"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="searchEmployees">
                  <el-icon><Search /></el-icon> 搜索
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 搜索结果 -->
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><User /></el-icon>
              <span>搜索结果</span>
            </div>
          </div>
          <div class="section-block__table">
            <el-table 
              v-loading="searchLoading" 
              :data="searchResults" 
              size="small"
              max-height="300"
            >
              <el-table-column prop="name" label="姓名" width="90" />
              <el-table-column prop="mobile" label="手机" width="120" />
              <el-table-column prop="email" label="邮箱" min-width="140" show-overflow-tooltip />
              <el-table-column label="当前部门" min-width="100" show-overflow-tooltip>
                <template #default="{ row }">
                  <span>{{ row.primary_dept_name || '未分配' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="center">
                <template #default="{ row }">
                  <el-button 
                    v-if="!isAlreadyInDept(row)"
                    type="primary" 
                    size="small" 
                    @click="handleAddExistingToDept(row)"
                  >
                    添加
                  </el-button>
                  <el-tag v-else type="info" size="mini">已在部门</el-tag>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="!searchLoading && searchResults.length === 0" class="section-block__empty">
              <el-empty description="暂无员工数据" :image-size="60" />
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="addToDeptDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 企业微信绑定对话框 -->
    <el-dialog 
      v-model="wechatBindDialogVisible" 
      :title="wechatBindMode === 'bind' ? '绑定企业微信' : '企业微信配置'" 
      width="560px"
      destroy-on-close
    >
      <div class="section-blocks" style="gap: 0;">
        <!-- 提示信息 -->
        <div v-if="wechatBindMode === 'bind'" class="section-block" style="margin-bottom: 16px;">
          <div class="section-block__content" style="padding: 12px 16px;">
            <div class="wechat-tips">
              <el-icon style="color: var(--el-color-info); font-size: var(--el-font-size-md);"><Info-Filled /></el-icon>
              <div class="wechat-tips__content">
                <div class="wechat-tips__title">请在企业微信管理后台获取以下配置信息</div>
                <div class="wechat-tips__desc">进入「管理工具 → 通讯录同步」获取 Secret；设置「接收事件服务器」获取 Token 和 EncodingAESKey</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 基础配置 -->
        <div class="section-block" style="margin-bottom: 16px;">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Connection /></el-icon>
              <span>基础配置</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="wechatForm" label-width="160px" :disabled="wechatBindMode === 'view'">
              <el-form-item label="企业 ID (corp_id)" required>
                <el-input v-model="wechatForm.corp_id" placeholder="如 wwxxxxxxxxxxxxxxxxxx" autocomplete="off" />
              </el-form-item>
              <el-form-item label="通讯录 Secret" required>
                <el-input v-model="wechatForm.corp_secret" placeholder="通讯录同步专用 Secret" show-password autocomplete="off" />
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 扫码登录配置 -->
        <div class="section-block" style="margin-bottom: 16px;">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Key /></el-icon>
              <span>扫码登录配置（可选）</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="wechatForm" label-width="160px" :disabled="wechatBindMode === 'view'">
              <el-form-item label="自建应用 AgentID">
                <el-input v-model="wechatForm.login_agent_id" placeholder="应用管理 → 自建应用 → AgentID" autocomplete="off" />
              </el-form-item>
              <el-form-item label="自建应用 Secret">
                <el-input v-model="wechatForm.login_secret" placeholder="自建应用的 Secret" show-password autocomplete="off" />
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 回调配置 -->
        <div class="section-block">
          <div class="section-block__header">
            <div class="section-block__title">
              <el-icon><Link /></el-icon>
              <span>回调配置（可选）</span>
            </div>
          </div>
          <div class="section-block__content">
            <el-form :model="wechatForm" label-width="160px" :disabled="wechatBindMode === 'view'">
              <el-form-item label="回调 Token">
                <el-input v-model="wechatForm.callback_token" placeholder="事件服务器 Token" autocomplete="off" />
              </el-form-item>
              <el-form-item label="EncodingAESKey">
                <el-input v-model="wechatForm.callback_aes_key" placeholder="事件服务器 EncodingAESKey" autocomplete="off" />
              </el-form-item>
              <el-form-item v-if="wechatBindMode !== 'view'" label="回调 URL">
                <el-input 
                  :model-value="wechatWebhookUrl" 
                  readonly 
                  disabled
                >
                  <template #append>
                    <el-button @click="copyWebhookUrl">复制</el-button>
                  </template>
                </el-input>
                <div style="font-size: var(--el-font-size-xs); color: var(--el-text-color-secondary); margin-top: 4px">
                  将此 URL 填入企业微信「接收事件服务器」的 URL 字段
                </div>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="wechatBindDialogVisible = false">
          {{ wechatBindMode === 'view' ? '关闭' : '取消' }}
        </el-button>
        <el-button 
          v-if="wechatBindMode === 'bind'" 
          type="primary" 
          @click="submitWechatBind" 
          :loading="wechatSubmitLoading"
        >
          验证并绑定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Folder, User, UserFilled, ArrowDown, Search, OfficeBuilding, Connection, Key, Link, InfoFilled, Remove, Collection } from '@element-plus/icons-vue'
import EmptyState from '@/components/EmptyState.vue'
import { organizationApi, departmentApi, employeeApi, wechatWorkApi } from '@/api'

// 组织列表
const organizations = ref([])
const currentOrgId = ref(null)
const currentOrg = computed(() => organizations.value.find(o => o.id === currentOrgId.value))

// 部门树
const departmentTree = ref([])
const deptLoading = ref(false)
const selectedDept = ref(null)
const deptTreeRef = ref(null)

// 部门员工
const deptEmployees = ref([])
const employeeLoading = ref(false)
const employeePagination = reactive({ page: 1, pageSize: 10, total: 0 })

// 对话框
const orgDialogVisible = ref(false)
const deptDialogVisible = ref(false)
const employeeDialogVisible = ref(false)
const addToDeptDialogVisible = ref(false)
const submitLoading = ref(false)

// 表单
const orgForm = reactive({ id: null, name: '', code: '', note: '' })
const deptForm = reactive({ id: null, name: '', parent_id: null, sort_order: 0 })
const employeeForm = reactive({ 
  id: null, name: '', mobile: '', email: '', gender: 0,
  emp_no: '', position: '', dept_id: null
})

// 筛选条件
const empStatusFilter = ref(null)
const accountStatusFilter = ref(null)

// 搜索
const searchKeyword = ref('')
const searchResults = ref([])
const searchLoading = ref(false)

// 企业微信绑定
const wechatBound = ref(false)
const wechatConfig = ref({})
const wechatBindDialogVisible = ref(false)
const wechatBindMode = ref('bind')  // 'bind' | 'view'
const wechatSubmitLoading = ref(false)
const wechatSyncLoading = ref(false)
const wechatForm = reactive({
  corp_id: '',
  corp_secret: '',
  login_agent_id: '',
  login_secret: '',
  callback_token: '',
  callback_aes_key: '',
})
const wechatWebhookUrl = computed(() => {
  const baseUrl = window.location.origin
  return currentOrgId.value
    ? `${baseUrl}/api/v1/wechat-work/webhook/${currentOrgId.value}`
    : ''
})

// 加载企微绑定状态
const loadWechatConfig = async () => {
  if (!currentOrgId.value) {
    wechatBound.value = false
    return
  }
  try {
    const res = await wechatWorkApi.getConfig(currentOrgId.value)
    wechatConfig.value = res.data || {}
    wechatBound.value = res.data?.is_bound || false
  } catch {
    wechatBound.value = false
  }
}

// 显示绑定对话框
const showWechatBindDialog = () => {
  wechatBindMode.value = 'bind'
  Object.assign(wechatForm, { corp_id: '', corp_secret: '', login_agent_id: '', login_secret: '', callback_token: '', callback_aes_key: '' })
  wechatBindDialogVisible.value = true
}

// 显示查看配置对话框
const showWechatConfigDialog = async () => {
  await loadWechatConfig()
  wechatBindMode.value = 'view'
  Object.assign(wechatForm, {
    corp_id: wechatConfig.value.corp_id || '',
    corp_secret: wechatConfig.value.corp_secret || '',
    login_agent_id: wechatConfig.value.login_agent_id || '',
    login_secret: wechatConfig.value.login_secret || '',
    callback_token: wechatConfig.value.callback_token || '',
    callback_aes_key: wechatConfig.value.callback_aes_key || '',
  })
  wechatBindDialogVisible.value = true
}

// 提交绑定
const submitWechatBind = async () => {
  if (!wechatForm.corp_id || !wechatForm.corp_secret) {
    ElMessage.warning('请填写企业 ID 和通讯录 Secret')
    return
  }
  wechatSubmitLoading.value = true
  try {
    await wechatWorkApi.bind({
      org_id: currentOrgId.value,
      ...wechatForm,
    })
    ElMessage.success('企业微信绑定成功')
    wechatBindDialogVisible.value = false
    await loadWechatConfig()
  } catch (e) {
    ElMessage.error(e.message || '绑定失败')
  } finally {
    wechatSubmitLoading.value = false
  }
}

// 解绑
const handleWechatUnbind = async () => {
  try {
    await ElMessageBox.confirm(
      '解绑后将无法接收企业微信通讯录变更通知，已同步的数据会保留。确认解绑？',
      '解绑企业微信',
      { type: 'warning' }
    )
    await wechatWorkApi.unbind({ org_id: currentOrgId.value })
    ElMessage.success('已解绑企业微信')
    await loadWechatConfig()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '解绑失败')
    }
  }
}

// 同步通讯录
const handleWechatSync = async () => {
  try {
    await ElMessageBox.confirm(
      '将从企业微信拉取完整通讯录并同步到本地，可能需要一些时间。确认同步？',
      '同步通讯录',
      { type: 'info' }
    )
    wechatSyncLoading.value = true
    const res = await wechatWorkApi.manualSync({ org_id: currentOrgId.value })
    const result = res.data || {}
    ElMessage.success(
      `同步完成：新建 ${result.created_count || 0}，更新 ${result.updated_count || 0}，` +
      `删除 ${result.deleted_count || 0}，耗时 ${(result.duration_seconds || 0).toFixed(1)}s`
    )
    // 刷新部门树和员工列表
    loadDeptTree()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '同步失败')
    }
  } finally {
    wechatSyncLoading.value = false
  }
}

// 复制回调 URL
const copyWebhookUrl = async () => {
  try {
    await navigator.clipboard.writeText(wechatWebhookUrl.value)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

// 加载组织列表
const loadOrganizations = async () => {
  try {
    const res = await organizationApi.list()
    // 组织列表接口返回分页格式 { rows, total_records, page, page_size }
    organizations.value = res.data?.rows || []
    if (organizations.value.length > 0 && !currentOrgId.value) {
      currentOrgId.value = organizations.value[0].id
      loadDeptTree()
      loadWechatConfig()
    }
  } catch (e) {
    ElMessage.error('加载组织列表失败')
  }
}

// 加载部门树
const loadDeptTree = async () => {
  if (!currentOrgId.value) return
  deptLoading.value = true
  try {
    const res = await departmentApi.tree(currentOrgId.value)
    departmentTree.value = res.data || []
  } catch (e) {
    ElMessage.error('加载部门树失败')
  } finally {
    deptLoading.value = false
  }
}

// 加载部门员工
const loadDeptEmployees = async () => {
  if (!selectedDept.value) return
  employeeLoading.value = true
  try {
    const params = {
      page: employeePagination.page,
      page_size: employeePagination.pageSize
    }
    if (empStatusFilter.value !== null && empStatusFilter.value !== '') {
      params.emp_status = empStatusFilter.value
    }
    if (accountStatusFilter.value !== null && accountStatusFilter.value !== '') {
      params.account_status = accountStatusFilter.value
    }
    const res = await departmentApi.getEmployees(selectedDept.value.id, params)
    deptEmployees.value = res.data?.rows || []
    employeePagination.total = res.data?.total_records || 0
  } catch (e) {
    ElMessage.error('加载员工列表失败')
  } finally {
    employeeLoading.value = false
  }
}

// 组织切换
const handleOrgChange = () => {
  selectedDept.value = null
  deptEmployees.value = []
  loadDeptTree()
  loadWechatConfig()
}

// 部门点击
const handleDeptClick = (data) => {
  selectedDept.value = data
  employeePagination.page = 1
  empStatusFilter.value = null
  accountStatusFilter.value = null
  loadDeptEmployees()
}

// 创建组织
const handleCreateOrg = () => {
  Object.assign(orgForm, { id: null, name: '', code: '', note: '' })
  orgDialogVisible.value = true
}

// 编辑组织
const handleEditOrg = () => {
  if (!currentOrg.value) return
  Object.assign(orgForm, currentOrg.value)
  orgDialogVisible.value = true
}

// 提交组织表单
const submitOrgForm = async () => {
  if (!orgForm.name || !orgForm.code) {
    ElMessage.warning('请填写必填项')
    return
  }
  submitLoading.value = true
  try {
    if (orgForm.id) {
      await organizationApi.update(orgForm.id, orgForm)
      ElMessage.success('更新成功')
    } else {
      const res = await organizationApi.create(orgForm)
      currentOrgId.value = res.data?.id
      ElMessage.success('创建成功')
    }
    orgDialogVisible.value = false
    loadOrganizations()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 创建部门
const handleCreateDept = (parent) => {
  Object.assign(deptForm, {
    id: null,
    name: '',
    parent_id: parent?.id || null,
    sort_order: 0
  })
  deptDialogVisible.value = true
}

// 编辑部门
const handleEditDept = (dept) => {
  Object.assign(deptForm, dept)
  deptDialogVisible.value = true
}

// 删除部门
const handleDeleteDept = async (dept) => {
  try {
    await ElMessageBox.confirm(`确定删除部门「${dept.name}」吗？`, '确认删除', { type: 'warning' })
    await departmentApi.delete(dept.id)
    ElMessage.success('删除成功')
    if (selectedDept.value?.id === dept.id) {
      selectedDept.value = null
      deptEmployees.value = []
    }
    loadDeptTree()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '删除失败')
  }
}

// 提交部门表单
const submitDeptForm = async () => {
  if (!deptForm.name) {
    ElMessage.warning('请输入部门名称')
    return
  }
  submitLoading.value = true
  try {
    if (deptForm.id) {
      await departmentApi.update(deptForm.id, deptForm)
      ElMessage.success('更新成功')
    } else {
      await departmentApi.create({ ...deptForm, org_id: currentOrgId.value })
      ElMessage.success('创建成功')
    }
    deptDialogVisible.value = false
    loadDeptTree()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 创建员工
const handleCreateEmployee = () => {
  Object.assign(employeeForm, {
    id: null, name: '', mobile: '', email: '', gender: 0,
    emp_no: '', position: '', dept_id: selectedDept.value?.id || null
  })
  employeeDialogVisible.value = true
}

// 编辑员工
const handleEditEmployee = (emp) => {
  Object.assign(employeeForm, {
    id: emp.id,
    name: emp.name,
    mobile: emp.mobile || '',
    email: emp.email || '',
    gender: emp.gender || 0
  })
  employeeDialogVisible.value = true
}

// 提交员工表单
const submitEmployeeForm = async () => {
  if (!employeeForm.name) {
    ElMessage.warning('请输入姓名')
    return
  }
  submitLoading.value = true
  try {
    if (employeeForm.id) {
      // 编辑
      await employeeApi.update(employeeForm.id, {
        name: employeeForm.name,
        mobile: employeeForm.mobile,
        email: employeeForm.email,
        gender: employeeForm.gender
      })
      ElMessage.success('更新成功')
    } else {
      // 新建员工
      const res = await employeeApi.create({
        name: employeeForm.name,
        mobile: employeeForm.mobile,
        email: employeeForm.email,
        gender: employeeForm.gender
      })
      const newEmpId = res.data?.id
      
      if (newEmpId && currentOrgId.value) {
        // 添加到组织
        await employeeApi.addToOrg({
          employee_id: newEmpId,
          org_id: currentOrgId.value,
          emp_no: employeeForm.emp_no,
          position: employeeForm.position,
          set_primary: true
        })
        
        // 添加到部门（如果选择了）
        if (employeeForm.dept_id) {
          await employeeApi.addToDept({
            employee_id: newEmpId,
            dept_id: employeeForm.dept_id,
            set_primary: true
          })
        }
      }
      ElMessage.success('创建成功')
    }
    
    employeeDialogVisible.value = false
    loadDeptTree()
    if (selectedDept.value) {
      loadDeptEmployees()
    }
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 添加员工到部门
const handleAddEmployeeToDept = async () => {
  searchKeyword.value = ''
  searchResults.value = []
  addToDeptDialogVisible.value = true
  // 自动加载员工列表
  await searchEmployees()
}

// 搜索员工（搜索所有员工，不限制组织，支持空关键词）
const searchEmployees = async () => {
  searchLoading.value = true
  try {
    const params = {
      page: 1,
      page_size: 20
    }
    // 如果有关键词才添加
    if (searchKeyword.value.trim()) {
      params.keyword = searchKeyword.value
    }
    const res = await employeeApi.list(params)
    searchResults.value = res.data?.rows || []
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    searchLoading.value = false
  }
}

// 检查员工是否已在当前部门
const isAlreadyInDept = (emp) => {
  return deptEmployees.value.some(e => e.id === emp.id)
}

// 添加已有员工到部门
const handleAddExistingToDept = async (emp) => {
  try {
    // 首先检查员工是否已在当前组织中
    const empDetail = await employeeApi.get(emp.id)
    const isInOrg = empDetail.data?.organizations?.some(o => o.org_id === currentOrgId.value)
    
    // 如果不在当前组织，先添加到组织
    if (!isInOrg) {
      await employeeApi.addToOrg({
        employee_id: emp.id,
        org_id: currentOrgId.value,
        set_primary: false
      })
    }

    // 然后添加到部门
    await employeeApi.addToDept({
      employee_id: emp.id,
      dept_id: selectedDept.value.id,
      set_primary: false
    })
    ElMessage.success(`已将「${emp.name}」添加到部门`)
    loadDeptEmployees()
    loadDeptTree()
    // 更新搜索结果中的状态
    searchResults.value = [...searchResults.value]
  } catch (e) {
    ElMessage.error(e.message || '添加失败')
  }
}

// 新建员工并添加到当前部门
const handleCreateAndAddEmployee = () => {
  addToDeptDialogVisible.value = false
  Object.assign(employeeForm, {
    id: null, name: '', mobile: '', email: '', gender: 0,
    emp_no: '', position: '', dept_id: selectedDept.value?.id
  })
  employeeDialogVisible.value = true
}

// 从部门移除员工
const handleRemoveFromDept = async (emp) => {
  try {
    await ElMessageBox.confirm(`确定将「${emp.name}」从部门移除吗？`, '确认移除', { type: 'warning' })
    await employeeApi.removeFromDept(emp.id, selectedDept.value.id)
    ElMessage.success('移除成功')
    loadDeptEmployees()
    loadDeptTree()
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

// 修改雇佣状态
const handleChangeEmpStatus = async (row, newStatus) => {
  if (row.status === newStatus) return
  try {
    await ElMessageBox.confirm(
      `确定将「${row.name}」的雇佣状态改为「${empStatusLabel(newStatus)}」吗？`,
      '确认修改', { type: 'warning' }
    )
    await employeeApi.updateOrgStatus(row.id, currentOrgId.value, newStatus)
    ElMessage.success('状态更新成功')
    loadDeptEmployees()
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
    loadDeptEmployees()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => {
  loadOrganizations()
})
</script>

<style scoped>
@import '../../styles/components/ui/tables.css';
.org-code-tag{
  margin-left: -22px;
  height: 32px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.main-content-row {
  display: flex;
  gap: 16px;
}
.department-card {
  flex: 0 0 360px;
  min-height: 500px;
  max-height: 620px;
  display: flex;
  flex-direction: column;
}

.department-card :deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.department-card :deep(.el-tree) {
  flex: 1;
  overflow-y: auto;
  max-height: calc(620px - 60px);
}
.data-card {
  flex: 1;
  min-height: 500px;
}

/* 员工列表卡片内部样式 */
.employee-list-card :deep(.el-card__body) {
  padding: 16px;
  background-color: var(--bodybg-color);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
}

.list-header h4 {
  margin: 0;
  font-size: var(--el-font-size-base);
  font-weight: var(--el-font-weight-extra-bold);
  color: var(--font-color);
}

.list-filter {
  background: var(--white);
  border-radius: var(--app-border-radius);
  padding: 12px 16px;
  margin-bottom: 12px;
  border: 1px solid var(--border_color);
}

.list-filter .filter-form {
  margin-bottom: 0;
}

.list-filter .filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 16px;
}

.list-filter .filter-form :deep(.el-form-item__label) {
  font-size: var(--el-font-size-xs);
}

/* 部门卡片头部样式 */
.dept-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.dept-card-header h3 {
  margin: 0;
  font-size: var(--el-font-size-md);
  font-weight: var(--el-font-weight-extra-bold);
}

.tree-node-content {
  display: flex;
  align-items: center;
  flex: 1;
  padding-right: 8px;
}
.dept-icon {
  margin-right: 6px;
  color: var(--el-color-primary);
}
.dept-name {
  flex: 1;
}
.dept-count {
  margin: 0 8px;
}
.dept-actions {
  opacity: 0;
  transition: opacity 0.2s;
}
.el-tree-node__content:hover .dept-actions {
  opacity: 1;
}
.employee-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-tag-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  cursor: pointer;
}
.status-arrow {
  font-size: var(--el-font-size-xs);
  color: var(--el-text-color-secondary);
}

@media (max-width: 1024px) {
  .main-content-row {
    flex-direction: column;
  }
  .department-card {
    flex: none;
  }
}

/* 企业微信绑定提示 */
.wechat-tips {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.wechat-tips__content {
  flex: 1;
}
.wechat-tips__title {
  font-size: var(--el-font-size-sm);
  color: var(--el-text-color-primary);
  line-height: var(--c-line-height-sm);
  margin-bottom: 2px;
}
.wechat-tips__desc {
  font-size: var(--el-font-size-xs);
  color: var(--el-text-color-secondary);
  line-height: var(--c-line-height-sm);
}

/* 添加员工到部门提示 */
.dept-tips {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.dept-tips__content {
  flex: 1;
}
.dept-tips__title {
  font-size: var(--el-font-size-sm);
  color: var(--el-text-color-primary);
  line-height: var(--c-line-height-sm);
  margin-bottom: 2px;
}
.dept-tips__desc {
  font-size: var(--el-font-size-xs);
  color: var(--el-text-color-secondary);
  line-height: var(--c-line-height-sm);
}
</style>
