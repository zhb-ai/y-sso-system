<template>
  <div class="stats-cards">
    <el-card class="stat-card" shadow="hover">
      <div class="stat-content">
        <div class="stat-info">
          <h3>{{ summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_FUNCTIONS] }}</h3>
          <p>缓存函数数</p>
        </div>
        <div class="stat-icon function">
          <el-icon><Collection /></el-icon>
        </div>
      </div>
    </el-card>

    <el-card class="stat-card" shadow="hover">
      <div class="stat-content">
        <div class="stat-info">
          <h3>{{ summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_HITS] }}</h3>
          <p>总命中次数</p>
        </div>
        <div class="stat-icon hit">
          <el-icon><CircleCheck /></el-icon>
        </div>
      </div>
    </el-card>

    <el-card class="stat-card" shadow="hover">
      <div class="stat-content">
        <div class="stat-info">
          <h3>{{ summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_MISSES] }}</h3>
          <p>总未命中次数</p>
        </div>
        <div class="stat-icon miss">
          <el-icon><CircleClose /></el-icon>
        </div>
      </div>
    </el-card>

    <el-card class="stat-card" shadow="hover">
      <div class="stat-content">
        <div class="stat-info">
          <h3>{{ formatSummaryHitRate(summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_HIT_RATE]) }}</h3>
          <p>总命中率</p>
        </div>
        <div class="stat-icon rate">
          <el-icon><TrendCharts /></el-icon>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { CircleCheck, CircleClose, Collection, TrendCharts } from "@element-plus/icons-vue";
import { CACHE_PAGE_KEYS } from "@/constants/cache";

defineProps({
  summary: { type: Object, default: () => ({}) },
});

const formatSummaryHitRate = (value) => `${Number(value || 0).toFixed(2)}%`;
</script>

<style scoped>
/* 统计卡片样式 - 参考仪表盘 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stats-cards .stat-card {
  border-radius: var(--app-border-radius);
  border: 1px solid var(--border_color);
  transition: var(--app-transition);
  background: rgb(var(--white));
  box-shadow: none;
}

.stats-cards .stat-card:hover {
  border-color: var(--el-color-primary-light-5);
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
}

.stat-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--font-title-color);
  line-height: 1.2;
}

.stat-info p {
  margin: 0;
  color: var(--font-light-color);
  font-size: var(--text-xs);
  font-weight: 500;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  transition: var(--app-transition);
  position: relative;
  overflow: hidden;
}

.stat-icon.function {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.stat-icon.hit {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.stat-icon.miss {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.stat-icon.rate {
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.stat-icon:hover {
  transform: translateY(-2px);
}

.stat-icon.function:hover {
  background: var(--el-color-primary-light-8);
}

.stat-icon.hit:hover {
  background: var(--el-color-success-light-8);
}

.stat-icon.miss:hover {
  background: var(--el-color-warning-light-8);
}

.stat-icon.rate:hover {
  background: var(--el-color-info-light-8);
}

/* 移动端紧凑布局：两列小卡片 */
@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
  }

  .stats-cards :deep(.el-card__body) {
    padding: 8px 10px;
  }

  .stats-cards .stat-content {
    padding: 0;
    gap: 6px;
  }

  .stats-cards .stat-info h3 {
    margin: 0;
    font-size: 16px;
    line-height: 1.2;
  }

  .stats-cards .stat-info p {
    font-size: 11px;
    line-height: 1.3;
  }

  .stats-cards .stat-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    font-size: 14px;
  }
}
</style>
