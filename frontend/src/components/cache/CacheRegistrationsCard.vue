<template>
  <el-card class="data-card registrations-card" shadow="hover">
    <template #header>
      <div class="card-header-with-switch">
        <div class="card-title">
          自动失效注册
          <el-tooltip
            content="启用后，ORM 模型发生 update/delete/insert 事件时会自动触发对应缓存失效。"
            placement="top"
          >
            <el-icon class="hint-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
        <div class="switch-area">
          <span class="switch-label">自动失效</span>
          <el-switch
            :model-value="enabled"
            :loading="loading"
            @change="(value) => emit('toggle', value)"
          />
        </div>
      </div>
    </template>

    <EmptyState
      v-if="modelList.length === 0"
      type="data"
      :icon="DataLine"
      title="暂无自动失效注册"
      description="当数据模型配置了自动失效缓存时，相关注册信息将显示在这里"
      compact
    />

    <el-collapse v-else>
      <el-collapse-item
        v-for="modelName in modelList"
        :key="modelName"
        :title="`${modelName}（${registrations[modelName].length}）`"
        :name="modelName"
      >
        <div
          v-for="(reg, idx) in registrations[modelName]"
          :key="`${modelName}-${reg.func}-${idx}`"
          class="registration-item"
        >
          <el-tag type="info" effect="plain">{{ reg.func }}</el-tag>
          <div class="events-wrap">
            <el-tag
              v-for="eventName in reg.events"
              :key="`${modelName}-${reg.func}-${eventName}`"
              type="success"
              effect="light"
              size="small"
            >
              {{ eventName }}
            </el-tag>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>

<script setup>
import { computed } from "vue";
import { DataLine, QuestionFilled } from "@element-plus/icons-vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({
  registrations: { type: Object, default: () => ({}) },
  enabled: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["toggle"]);

const modelList = computed(() => Object.keys(props.registrations || {}));
</script>

<style scoped>
.registrations-card {
  margin-top: var(--spacing-medium);
}

.registrations-card:hover {
  border-color: var(--border_color);
  box-shadow: none;
  transform: none;
}

.card-header-with-switch {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.card-title {
  color: var(--font-title-color);
  font-size: var(--el-font-size-base);
  font-weight: var(--el-font-weight-extra-bold);
}

.switch-area {
  align-items: center;
  display: flex;
  gap: 8px;
}

.switch-label {
  color: var(--font-medium-color);
  font-size: var(--el-font-size-sm);
}

.hint-icon {
  color: var(--font-light-color);
  cursor: pointer;
  font-size: 12px;
  margin-left: 6px;
  transition: var(--app-transition);
  vertical-align: middle;
}

.hint-icon:hover {
  color: var(--el-color-primary);
}

.registration-item {
  align-items: center;
  border-bottom: 1px dashed var(--border_color);
  display: flex;
  gap: 12px;
  justify-content: space-between;
  padding: 10px 0;
}

.registration-item:last-child {
  border-bottom: none;
}

.events-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (max-width: 768px) {
  .registrations-card {
    margin-top: 12px;
    margin-bottom: 0;
  }

  .registrations-card :deep(.el-card__header) {
    padding: 12px 14px;
  }

  .registrations-card :deep(.el-card__body) {
    padding: 4px 14px;
  }

  .switch-label {
    font-size: var(--el-font-size-xs);
  }
}
</style>
