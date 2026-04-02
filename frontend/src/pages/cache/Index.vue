<template>
  <div class="page-container">
    <div class="page-header">
      <h2>
        缓存管理
        <el-tooltip
          content="可查看缓存函数、统计与条目预览；条目值默认仅展示脱敏预览，不返回原始敏感数据。"
          placement="top"
        >
          <el-icon class="hint-icon"><QuestionFilled /></el-icon>
        </el-tooltip>
      </h2>
      <div class="header-actions">
        <el-button class="btn-reset" @click="loadAllData" :loading="loading">
          <el-icon><RefreshRight /></el-icon> 刷新
        </el-button>
        <el-button type="danger" @click="handleClearAll" :loading="clearingAll">
          <el-icon><Delete /></el-icon> 清空全部缓存
          <el-tooltip
            content="将清空所有已注册缓存函数的数据，建议仅在发布后或排障时使用。"
            placement="top"
          >
            <el-icon class="hint-icon btn-hint-icon"
              ><QuestionFilled
            /></el-icon>
          </el-tooltip>
        </el-button>
      </div>
    </div>

    <el-row :gutter="16" class="summary-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="summary-card" shadow="hover">
          <div class="summary-title">缓存函数数</div>
          <div class="summary-value">
            {{ summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_FUNCTIONS] }}
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="summary-card" shadow="hover">
          <div class="summary-title">总命中次数</div>
          <div class="summary-value">
            {{ summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_HITS] }}
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="summary-card" shadow="hover">
          <div class="summary-title">总未命中次数</div>
          <div class="summary-value">
            {{ summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_MISSES] }}
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="summary-card" shadow="hover">
          <div class="summary-title">总命中率</div>
          <div class="summary-value">
            {{
              formatSummaryHitRate(
                summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_HIT_RATE],
              )
            }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-alert
      class="page-hint-alert compact-hint-alert"
      type="info"
      :closable="false"
      show-icon
      description="建议先通过“函数列表/统计”定位目标，再查看“缓存条目”详情。条目值只展示脱敏预览。"
    />

    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" class="filter-form">
        <el-form-item>
          <template #label
            >函数名<el-tooltip
              content="用于筛选并查看某个缓存函数的统计与条目详情。"
              placement="top"
            >
              <el-icon class="hint-icon form-item-hint"
                ><QuestionFilled
              /></el-icon>
            </el-tooltip>
          </template>
          <el-select
            v-model="selectedFunctionName"
            filterable
            clearable
            placeholder="请选择缓存函数"
            style="min-width: 260px"
          >
            <el-option
              v-for="item in functions"
              :key="item[CACHE_FUNCTION_COLUMNS.NAME]"
              :label="item[CACHE_FUNCTION_COLUMNS.NAME]"
              :value="item[CACHE_FUNCTION_COLUMNS.NAME]"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleViewSingleStats()"
            :disabled="!selectedFunctionName"
          >
            查看单函数统计
          </el-button>
          <el-button class="btn-reset" @click="selectedFunctionName = ''">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="data-card" shadow="hover">
      <el-table
        v-loading="loading"
        :data="functions"
        row-key="name"
        style="width: 100%"
      >
        <el-table-column
          :prop="CACHE_FUNCTION_COLUMNS.NAME"
          label="函数名"
          min-width="180"
        />
        <el-table-column
          :prop="CACHE_FUNCTION_COLUMNS.MODULE"
          label="模块"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column
          :prop="CACHE_FUNCTION_COLUMNS.BACKEND"
          label="后端"
          width="120"
          align="center"
        >
          <template #default="scope">
            <el-tag
              :type="
                getBackendTagType(scope.row[CACHE_FUNCTION_COLUMNS.BACKEND])
              "
              effect="light"
            >
              {{ scope.row[CACHE_FUNCTION_COLUMNS.BACKEND] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :prop="CACHE_FUNCTION_COLUMNS.TTL"
          label="TTL(秒)"
          width="120"
          align="center"
        />
        <el-table-column
          :prop="CACHE_FUNCTION_COLUMNS.KEY_PREFIX"
          label="Key 前缀"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column width="180" align="center">
          <template #header>
            <span>
              命中/未命中
              <el-tooltip
                content="统计值来自当前服务运行期内累计数据，重启服务后可能重置。"
                placement="top"
              >
                <el-icon class="hint-icon table-header-hint"
                  ><QuestionFilled
                /></el-icon>
              </el-tooltip>
            </span>
          </template>
          <template #default="scope">
            <span
              >{{ getFunctionHits(scope.row) }}/{{
                getFunctionMisses(scope.row)
              }}</span
            >
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="180"
          align="center"
          class-name="table-cell-flex-center"
        >
          <template #default="scope">
            <el-button
              type="info"
              link
              size="small"
              @click="handleViewEntries(scope.row.name)"
            >
              条目
            </el-button>
            <el-button
              type="primary"
              link
              size="small"
              @click="handleViewSingleStats(scope.row.name)"
            >
              统计
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleClearOne(scope.row.name)"
            >
              清空
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

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
              :model-value="invalidatorEnabled"
              :loading="toggleLoading"
              @change="handleToggleInvalidator"
            />
          </div>
        </div>
      </template>

      <EmptyState
        v-if="registrationModelList.length === 0"
        type="data"
        :icon="DataLine"
        title="暂无自动失效注册"
        description="当数据模型配置了自动失效缓存时，相关注册信息将显示在这里"
        compact
      />

      <el-collapse v-else>
        <el-collapse-item
          v-for="modelName in registrationModelList"
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

    <el-dialog
      v-model="singleStatsDialogVisible"
      title="缓存函数统计"
      width="520px"
      align-center
    >
      <el-descriptions :column="1" border v-if="singleStats">
        <el-descriptions-item label="函数">{{
          singleStats.function || "-"
        }}</el-descriptions-item>
        <el-descriptions-item label="后端">{{
          singleStats.backend || "-"
        }}</el-descriptions-item>
        <el-descriptions-item label="TTL(秒)">{{
          singleStats.ttl ?? "-"
        }}</el-descriptions-item>
        <el-descriptions-item label="命中次数">{{
          singleStats.hits ?? 0
        }}</el-descriptions-item>
        <el-descriptions-item label="未命中次数">{{
          singleStats.misses ?? 0
        }}</el-descriptions-item>
        <el-descriptions-item label="命中率">{{
          singleStats.hit_rate || "-"
        }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="singleStatsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="entriesDialogVisible"
      :title="`缓存条目 - ${entriesFunctionName || '-'}`"
      width="900px"
      align-center
      destroy-on-close
    >
      <el-alert
        class="dialog-hint-alert compact-hint-alert"
        type="info"
        :closable="false"
        show-icon
        description="点击“详情”可查看该 Key 的元信息与脱敏值预览；TTL 为“-”通常表示后端不提供剩余时间。"
      />

      <div class="data-card dialog-table-card">
        <el-table
          v-loading="entriesLoading"
          :data="entriesList"
          row-key="key"
          style="width: 100%"
        >
          <el-table-column
            prop="key"
            label="Key"
            min-width="280"
            show-overflow-tooltip
          />
          <el-table-column
            prop="ttl_remaining"
            label="剩余TTL(秒)"
            width="140"
            align="center"
          >
            <template #default="scope">
              {{ scope.row.ttl_remaining ?? "-" }}
            </template>
          </el-table-column>
          <el-table-column
            prop="value_type"
            label="值类型"
            width="120"
            align="center"
          />
          <el-table-column
            prop="value_size"
            label="大小"
            width="120"
            align="center"
          >
            <template #default="scope">
              {{ formatSize(scope.row.value_size) }}
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="100"
            align="center"
            class-name="table-cell-flex-center"
          >
            <template #default="scope">
              <el-button
                type="primary"
                link
                size="small"
                @click="handleViewEntryDetail(scope.row.key)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="entry-detail-block" v-loading="entryDetailLoading">
        <div class="entry-detail-header">
          <div class="entry-detail-title">条目详情（脱敏预览）</div>
          <el-tooltip
            content="详情仅展示脱敏预览；密码、密钥、Token 等敏感字段会显示为 ***。"
            placement="top"
          >
            <el-icon class="hint-icon entry-detail-hint"
              ><QuestionFilled
            /></el-icon>
          </el-tooltip>
        </div>
        <EmptyState
          v-if="!entryDetail"
          type="data"
          :icon="Collection"
          title="请选择缓存条目"
          description="点击上方列表中的条目，查看详细的缓存数据和元信息"
          compact
        />
        <template v-else>
          <el-descriptions :column="2" border class="entry-detail-meta">
            <el-descriptions-item label="Key">{{
              entryDetail.key
            }}</el-descriptions-item>
            <el-descriptions-item label="值类型">{{
              entryDetail.value_type
            }}</el-descriptions-item>
            <el-descriptions-item label="剩余TTL">{{
              entryDetail.ttl_remaining ?? "-"
            }}</el-descriptions-item>
            <el-descriptions-item label="大小">{{
              formatSize(entryDetail.value_size)
            }}</el-descriptions-item>
          </el-descriptions>
          <div class="preview-title">值预览</div>
          <pre class="preview-json">{{
            formatPreview(entryDetail.value_preview)
          }}</pre>
        </template>
      </div>

      <template #footer>
        <el-button @click="entriesDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Delete, QuestionFilled, RefreshRight, Collection, DataLine } from "@element-plus/icons-vue";
import { cacheApi } from "@/api";
import { handleApiError, getDefaultErrorMessage } from "@/utils/errorHandler";
import EmptyState from "@/components/EmptyState.vue";
import {
  CACHE_BACKEND_TAG_TYPE,
  CACHE_FUNCTION_COLUMNS,
  CACHE_PAGE_KEYS,
} from "@/constants/cache";

const loading = ref(false);
const clearingAll = ref(false);
const toggleLoading = ref(false);
const selectedFunctionName = ref("");
const singleStatsDialogVisible = ref(false);
const singleStats = ref(null);
const entriesDialogVisible = ref(false);
const entriesLoading = ref(false);
const entriesFunctionName = ref("");
const entriesList = ref([]);
const entryDetailLoading = ref(false);
const entryDetail = ref(null);

const functions = ref([]);
const registrations = ref({});
const invalidatorEnabled = ref(true);

const summary = reactive({
  [CACHE_PAGE_KEYS.SUMMARY_TOTAL_FUNCTIONS]: 0,
  [CACHE_PAGE_KEYS.SUMMARY_TOTAL_HITS]: 0,
  [CACHE_PAGE_KEYS.SUMMARY_TOTAL_MISSES]: 0,
  [CACHE_PAGE_KEYS.SUMMARY_TOTAL_HIT_RATE]: 0,
});

const perFunctionStats = ref({});

const registrationModelList = computed(() => Object.keys(registrations.value));

const formatSummaryHitRate = (value) => `${Number(value || 0).toFixed(2)}%`;
const formatPreview = (value) => JSON.stringify(value ?? null, null, 2);
const formatSize = (size) => {
  const bytes = Number(size || 0);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const getBackendTagType = (backend) =>
  CACHE_BACKEND_TAG_TYPE[backend] || "info";

const getFunctionHits = (item) => {
  let key = item.name;
  for (const k in perFunctionStats.value) {
    if (k.indexOf(item.module) !== -1 && perFunctionStats.value[k]?.function === key) {
      return perFunctionStats.value[k]?.hits ?? 0;
    }
  }
  return 0;
};
const getFunctionMisses = (item) => {
  let key = item.name;
  for (const k in perFunctionStats.value) {
    if (k.indexOf(item.module) !== -1 && perFunctionStats.value[k]?.function === key) {
      return perFunctionStats.value[k]?.misses ?? 0;
    }
  }
  return 0;
};

const loadFunctions = async () => {
  const res = await cacheApi.listFunctions();
  const data = res?.data || {};
  functions.value = data.functions || [];
};

const loadStats = async () => {
  const res = await cacheApi.getStats();
  const data = res?.data || {};

  summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_FUNCTIONS] = data.total_functions || 0;
  summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_HITS] = data.total_hits || 0;
  summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_MISSES] = data.total_misses || 0;
  summary[CACHE_PAGE_KEYS.SUMMARY_TOTAL_HIT_RATE] = data.total_hit_rate || 0;
  perFunctionStats.value = data.functions || {};
};

const loadRegistrations = async () => {
  const res = await cacheApi.getInvalidatorRegistrations();
  const data = res?.data || {};
  invalidatorEnabled.value = data.enabled !== false;
  registrations.value = data.registrations || {};
};

const loadAllData = async () => {
  loading.value = true;
  try {
    await Promise.all([loadFunctions(), loadStats(), loadRegistrations()]);
  } catch (error) {
    handleApiError(error, getDefaultErrorMessage("get"));
  } finally {
    loading.value = false;
  }
};

const handleClearOne = async (functionName) => {
  try {
    await ElMessageBox.confirm(
      `确定要清空函数「${functionName}」的缓存吗？`,
      "清空确认",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning" },
    );
    await cacheApi.clear(functionName);
    ElMessage.success("缓存清空成功");
    await loadAllData();
  } catch (error) {
    if (error !== "cancel") {
      handleApiError(error, getDefaultErrorMessage("delete"));
    }
  }
};

const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm(
      "确定要清空全部缓存吗？该操作会影响所有已注册缓存函数。",
      "清空确认",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning" },
    );
    clearingAll.value = true;
    await cacheApi.clear();
    ElMessage.success("全部缓存已清空");
    await loadAllData();
  } catch (error) {
    if (error !== "cancel") {
      handleApiError(error, getDefaultErrorMessage("delete"));
    }
  } finally {
    clearingAll.value = false;
  }
};

const handleViewSingleStats = async (
  functionName = selectedFunctionName.value,
) => {
  const normalizedFunctionName =
    typeof functionName === "string"
      ? functionName
      : selectedFunctionName.value;

  if (!normalizedFunctionName) {
    ElMessage.warning("请先选择缓存函数");
    return;
  }
  try {
    const res = await cacheApi.getStats(normalizedFunctionName);
    singleStats.value = res?.data || {};
    singleStatsDialogVisible.value = true;
  } catch (error) {
    handleApiError(error, getDefaultErrorMessage("get"));
  }
};

const handleViewEntries = async (functionName) => {
  entriesFunctionName.value = functionName;
  entriesDialogVisible.value = true;
  entriesLoading.value = true;
  entryDetail.value = null;
  try {
    const res = await cacheApi.listEntries(functionName, 100);
    entriesList.value = res?.data?.entries || [];
  } catch (error) {
    entriesList.value = [];
    handleApiError(error, getDefaultErrorMessage("get"));
  } finally {
    entriesLoading.value = false;
  }
};

const handleViewEntryDetail = async (key) => {
  if (!entriesFunctionName.value) return;
  entryDetailLoading.value = true;
  try {
    const res = await cacheApi.getEntry(entriesFunctionName.value, key);
    entryDetail.value = res?.data || null;
  } catch (error) {
    entryDetail.value = null;
    handleApiError(error, getDefaultErrorMessage("get"));
  } finally {
    entryDetailLoading.value = false;
  }
};

const handleToggleInvalidator = async (enabled) => {
  toggleLoading.value = true;
  try {
    await cacheApi.toggleInvalidator(Boolean(enabled));
    invalidatorEnabled.value = Boolean(enabled);
    ElMessage.success(`自动失效已${enabled ? "启用" : "禁用"}`);
  } catch (error) {
    invalidatorEnabled.value = !enabled;
    handleApiError(error, "切换自动失效失败");
  } finally {
    toggleLoading.value = false;
  }
};

onMounted(() => {
  loadAllData();
});
</script>

<style scoped>

/* 紧凑提示条（用于页面说明/弹窗说明） */
.compact-hint-alert .el-alert__icon {
  font-size: 14px;
}

.compact-hint-alert .el-alert__description {
  font-size: 12px;
  line-height: 1.5;
}
/* 页面内帮助提示图标（问号/叹号） */
.hint-icon {
  color: var(--font-light-color);
  cursor: pointer;
  font-size: 12px;
  margin-left: 6px;
  transition: var(--app-transition);
  vertical-align: middle;
}

.hint-icon:hover {
  color: rgba(var(--primary), 1);
}

.page-header-actions {
  display: flex;
  gap: var(--spacing-small);
}

.page-hint-alert {
  margin-bottom: var(--spacing-medium);
}

.btn-hint-icon {
  color: inherit;
  margin-left: 4px;
}

.btn-hint-icon:hover {
  color: inherit;
  opacity: 0.85;
}

.form-item-hint {
  margin-right: 6px;
}

.table-header-hint {
  font-size: var(--el-font-size-xs);
  margin-left: 4px;
}

.summary-row {
  margin-bottom: var(--spacing-medium);
}

.summary-card {
  border: 1px solid var(--border_color);
}

.summary-title {
  color: var(--font-medium-color);
  font-size: var(--el-font-size-xs);
  margin-bottom: 8px;
}

.summary-value {
  color: var(--font-title-color);
  font-size: var(--el-font-size-xxl);
  font-weight: var(--el-font-weight-extra-bold);
  line-height: var(--c-line-height-xs);
}

.registrations-card {
  margin-top: var(--spacing-medium);
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

.dialog-hint-alert {
  margin-bottom: var(--spacing-small);
}

.dialog-table-card {
  border: 1px solid var(--border_color);
  box-shadow: none;
}

.dialog-table-card:hover {
  border-color: var(--border_color);
  box-shadow: none;
  transform: none;
}

.entry-detail-block {
  border-top: 1px solid var(--border_color);
  margin-top: var(--spacing-medium);
  min-height: 120px;
  padding-top: var(--spacing-medium);
}

.entry-detail-title {
  color: var(--font-title-color);
  font-size: var(--el-font-size-base);
  font-weight: var(--el-font-weight-extra-bold);
  margin-bottom: 8px;
}

.entry-detail-header {
  align-items: center;
  display: flex;
}

.entry-detail-hint {
  margin-bottom: 8px;
  margin-left: 4px;
}

.entry-detail-meta {
  margin-bottom: 10px;
}

.preview-title {
  color: var(--font-medium-color);
  font-size: var(--el-font-size-sm);
  margin-bottom: 6px;
}

.preview-json {
  background: var(--light-gray);
  border: 1px solid var(--border_color);
  border-radius: var(--border-radius);
  color: var(--font-color);
  font-family: var(--font-family-mono);
  font-size: var(--el-font-size-xs);
  line-height: var(--c-line-height-md);
  margin: 0;
  max-height: 260px;
  overflow: auto;
  padding: 10px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
