<template>
  <div class="page-container">
    <div class="page-header">
      <h2>部门管理</h2>
    </div>
    
    <!-- 提示信息 -->
    <el-card shadow="hover">
      <el-result icon="info" title="部门管理已整合到组织架构页面">
        <template #sub-title>
          <p>请前往「组织架构」页面进行部门的增删改查操作</p>
        </template>
        <template #extra>
          <el-button type="primary" @click="goToOrganization">
            前往组织架构
          </el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToOrganization = () => {
  router.push('/organization')
}
</script>
