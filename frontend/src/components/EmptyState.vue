<template>
  <div class="empty-state" :class="[`empty-state--${type}`, { 'empty-state--compact': compact }]">
    <div class="empty-state__icon">
      <el-icon v-if="icon">
        <component :is="icon" />
      </el-icon>
      <slot v-else name="icon">
        <el-icon><Collection /></el-icon>
      </slot>
    </div>
    
    <div class="empty-state__content">
      <h3 class="empty-state__title">{{ title }}</h3>
      <p v-if="description" class="empty-state__description">{{ description }}</p>
      <slot name="description"></slot>
    </div>
    
    <div v-if="$slots.action || actionText" class="empty-state__action">
      <slot name="action">
        <el-button v-if="actionText" :type="actionType" @click="$emit('action')">
          <el-icon v-if="actionIcon"><component :is="actionIcon" /></el-icon>
          {{ actionText }}
        </el-button>
      </slot>
    </div>
    
    <div v-if="$slots.extra" class="empty-state__extra">
      <slot name="extra"></slot>
    </div>
  </div>
</template>

<script setup>
/**
 * 空状态组件
 * @description 用于展示空数据状态，提供友好的引导和操作入口
 */

defineProps({
  /**
   * 空状态类型
   * @values data, search, error, permission, create, network
   */
  type: {
    type: String,
    default: 'data'
  },
  /**
   * 图标组件
   */
  icon: {
    type: [String, Object],
    default: null
  },
  /**
   * 标题
   */
  title: {
    type: String,
    default: '暂无数据'
  },
  /**
   * 描述文本
   */
  description: {
    type: String,
    default: ''
  },
  /**
   * 操作按钮文本
   */
  actionText: {
    type: String,
    default: ''
  },
  /**
   * 操作按钮类型
   */
  actionType: {
    type: String,
    default: 'primary'
  },
  /**
   * 操作按钮图标
   */
  actionIcon: {
    type: [String, Object],
    default: null
  },
  /**
   * 是否紧凑模式
   */
  compact: {
    type: Boolean,
    default: false
  }
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-state--compact {
  padding: 24px;
}

.empty-state__icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--el-color-primary-light-9);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  border: 2px solid var(--el-color-primary-light-5);
  animation: float 3s ease-in-out infinite;
}

.empty-state__icon .el-icon {
  font-size: 40px;
  color: var(--el-color-primary);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.empty-state--compact .empty-state__icon {
  width: 56px;
  height: 56px;
  margin-bottom: 16px;
}

.empty-state--compact .empty-state__icon .el-icon {
  font-size: 28px;
}

.empty-state__title {
  font-size: 14px;
  font-weight: 500;
  color: var(--font-title-color);
  margin: 0 0 8px;
}

.empty-state__description {
  font-size: 12px;
  color: var(--font-color);
  margin: 0 0 20px;
  max-width: 400px;
  line-height: 1.6;
}

.empty-state--compact .empty-state__description {
  margin-bottom: 16px;
}

.empty-state__action {
  display: flex;
  gap: 12px;
  align-items: center;
}

.empty-state__extra {
  margin-top: 16px;
  font-size: 13px;
  color: var(--font-light-color);
}

/* 搜索空状态 - 使用主题色 */
.empty-state--search .empty-state__icon {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
}

.empty-state--search .empty-state__icon .el-icon {
  color: var(--el-color-primary);
}

/* 错误空状态 - 使用主题色 */
.empty-state--error .empty-state__icon {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
}

.empty-state--error .empty-state__icon .el-icon {
  color: var(--el-color-primary);
}

/* 权限空状态 - 使用主题色 */
.empty-state--permission .empty-state__icon {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
}

.empty-state--permission .empty-state__icon .el-icon {
  color: var(--el-color-primary);
}

/* 创建/首次使用空状态 - 使用主题色 */
.empty-state--create .empty-state__icon {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
}

.empty-state--create .empty-state__icon .el-icon {
  color: var(--el-color-primary);
}

/* 网络错误空状态 - 使用灰色系 */
.empty-state--network .empty-state__icon {
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color);
}

.empty-state--network .empty-state__icon .el-icon {
  color: var(--el-text-color-secondary);
}
</style>
