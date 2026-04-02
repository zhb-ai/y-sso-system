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
  background: linear-gradient(135deg, #e8f7f9 0%, #f4fbfc 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  border: 2px solid rgba(72, 190, 206, 0.2);
  animation: float 3s ease-in-out infinite;
}

.empty-state__icon .el-icon {
  font-size: 40px;
  color: #48bece;
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
  font-size: 16px;
  font-weight: 500;
  color: var(--font-title-color);
  margin: 0 0 8px;
}

.empty-state__description {
  font-size: 14px;
  color: var(--font-light-color);
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

/* 搜索空状态 - 使用紫色系 */
.empty-state--search .empty-state__icon {
  background: linear-gradient(135deg, #f0f0fd 0%, #f8f8fe 100%);
  border-color: rgba(83, 90, 231, 0.2);
}

.empty-state--search .empty-state__icon .el-icon {
  color: #535ae7;
}

/* 错误空状态 - 使用红色系 */
.empty-state--error .empty-state__icon {
  background: linear-gradient(135deg, #fceae7 0%, #fef5f3 100%);
  border-color: rgba(229, 94, 64, 0.2);
}

.empty-state--error .empty-state__icon .el-icon {
  color: #e55e40;
}

/* 权限空状态 - 使用橙色系 */
.empty-state--permission .empty-state__icon {
  background: linear-gradient(135deg, #fcf6e6 0%, #fefbf3 100%);
  border-color: rgba(235, 195, 63, 0.2);
}

.empty-state--permission .empty-state__icon .el-icon {
  color: #d4a72c;
}

/* 创建/首次使用空状态 - 使用绿色系 */
.empty-state--create .empty-state__icon {
  background: linear-gradient(135deg, #f0f9e8 0%, #f7fcf4 100%);
  border-color: rgba(174, 204, 52, 0.2);
}

.empty-state--create .empty-state__icon .el-icon {
  color: #aecc34;
}

/* 网络错误空状态 - 使用灰色系 */
.empty-state--network .empty-state__icon {
  background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%);
  border-color: rgba(139, 132, 118, 0.2);
}

.empty-state--network .empty-state__icon .el-icon {
  color: #8b8476;
}
</style>
