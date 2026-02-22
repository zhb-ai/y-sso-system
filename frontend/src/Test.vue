<template>
  <div class="test-container">
    <h1>测试页面</h1>
    <p>如果能看到这个页面，说明Vue和路由配置是正常的。</p>
    <el-button type="primary" @click="goToLogin">前往登录页面</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToLogin = () => {
  router.push('/admin/login')
}
</script>

<style scoped>
.test-container {
  padding: 20px;
  text-align: center;
}
</style>