<template>
  <div class="error-container">
    <div class="error-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">页面未找到</h2>
      <p class="error-message">抱歉，您访问的页面不存在或已被删除。</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--bodybg-color);
}

.error-content {
  text-align: center;
  background-color: var(--white);
  padding: 3rem 2rem;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--hover-shadow);
  border: 1px solid var(--border_color);
  max-width: 480px;
  width: 100%;
}

.error-code {
  font-size: 6rem;
  font-weight: var(--el-font-weight-extra-bold);
  margin: 0 0 1.5rem 0;
  color: rgba(var(--primary), 1);
  line-height: var(--c-line-height-xs);
}

.error-title {
  font-size: var(--el-font-size-xxl);
  font-weight: var(--el-font-weight-extra-bold);
  margin: 0 0 1rem 0;
  color: var(--font-title-color);
}

.error-message {
  font-size: var(--el-font-size-base);
  color: var(--font-color);
  margin: 0 0 2rem 0;
  line-height: var(--c-line-height-md);
}

:deep(.el-button--primary) {
  background-color: rgba(var(--primary), 1);
  border-color: rgba(var(--primary), 1);
  border-radius: var(--border-radius);
  transition: all 0.2s ease;
  box-shadow: none;
  padding: 0.625rem 1.5rem;
  font-size: var(--el-font-size-base);
  font-weight: var(--el-font-weight-bold);
}

:deep(.el-button--primary:hover) {
  background-color: rgba(var(--primary), 0.9);
  border-color: rgba(var(--primary), 0.9);
  box-shadow: var(--hover-shadow);
  transform: translateY(-1px);
}
</style>