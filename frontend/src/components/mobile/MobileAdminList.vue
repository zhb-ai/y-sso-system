<template>
  <div class="mobile-admin" v-loading="loading">
    <div v-if="searchable || filterable || $slots.leading" class="m-toolbar">
      <div v-if="$slots.leading" class="m-toolbar__leading">
        <slot name="leading" />
      </div>
      <el-input
        v-if="searchable"
        v-model="keyword"
        class="m-toolbar__search"
        :placeholder="searchPlaceholder"
        clearable
        @clear="emit('search')"
        @keyup.enter="emit('search')"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button
        v-if="filterable"
        circle
        class="m-filter-btn"
        :class="{ 'is-active': filterActive }"
        aria-label="筛选"
        @click="filterOpen = true"
      >
        <el-icon><Filter /></el-icon>
      </el-button>
    </div>

    <slot name="tabs" />
    <slot name="header" />

    <div v-if="empty" class="m-list">
      <slot name="empty" />
    </div>
    <div v-else class="m-list">
      <slot />
    </div>

    <div v-if="infinite && !empty" class="m-load-status">
      <span v-if="loadingMore">加载中...</span>
      <span v-else-if="finished">没有更多了</span>
    </div>
    <div v-if="infinite && !empty" ref="sentinelRef" class="m-load-sentinel"></div>

    <div v-if="$slots.footer && !infinite" class="m-pager">
      <slot name="footer" />
    </div>

    <div v-if="pageActions.length" class="m-bottom-bar">
      <el-button
        v-for="action in visiblePageActions"
        :key="action.key || action.label"
        class="btn-modern"
        :type="action.type || 'default'"
        :disabled="action.disabled"
        :loading="action.loading"
        @click="action.onClick?.()"
      >
        <el-icon v-if="action.icon"><component :is="action.icon" /></el-icon>
        {{ action.label }}
      </el-button>
      <el-button v-if="overflowPageActions.length" class="btn-modern" @click="pageMoreOpen = true">
        <el-icon><MoreFilled /></el-icon>
        更多
      </el-button>
    </div>

    <MobileActionSheet
      v-if="filterable"
      v-model="filterOpen"
      title="筛选"
      subtitle="设置筛选条件"
    >
      <slot name="filter" />
      <template #footer>
        <el-button class="btn-reset" @click="emit('reset')">重置</el-button>
        <el-button type="primary" class="btn-modern" @click="filterOpen = false">查询</el-button>
      </template>
    </MobileActionSheet>

    <MobileActionSheet v-model="pageMoreOpen" title="更多操作" :items="overflowPageActions" />
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { Filter, MoreFilled, Search } from "@element-plus/icons-vue";
import MobileActionSheet from "./MobileActionSheet.vue";

const props = defineProps({
  searchable: { type: Boolean, default: true },
  searchPlaceholder: { type: String, default: "搜索" },
  filterable: { type: Boolean, default: false },
  filterActive: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  empty: { type: Boolean, default: false },
  infinite: { type: Boolean, default: false },
  loadingMore: { type: Boolean, default: false },
  finished: { type: Boolean, default: false },
  pageActions: { type: Array, default: () => [] },
});

const keyword = defineModel("keyword", { type: String, default: "" });
const emit = defineEmits(["search", "reset", "query", "load-more"]);

const filterOpen = ref(false);
const pageMoreOpen = ref(false);
const sentinelRef = ref(null);
let loadObserver = null;

const findScrollParent = (el) => {
  let node = el.parentElement;
  while (node) {
    const overflow = getComputedStyle(node).overflowY;
    if (overflow === "auto" || overflow === "scroll") return node;
    node = node.parentElement;
  }
  return null;
};

const askLoadMore = () => {
  if (!props.infinite || props.empty || props.loading || props.loadingMore || props.finished) return;
  emit("load-more");
};

const bindLoadObserver = () => {
  loadObserver?.disconnect();
  loadObserver = null;
  const el = sentinelRef.value;
  if (!el || !props.infinite) return;
  loadObserver = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) askLoadMore();
    },
    { root: findScrollParent(el), rootMargin: "120px" },
  );
  loadObserver.observe(el);
};

const visiblePageActions = computed(() =>
  props.pageActions.length > 2 ? props.pageActions.slice(0, 2) : props.pageActions,
);
const overflowPageActions = computed(() =>
  props.pageActions.length > 2 ? props.pageActions.slice(2) : [],
);

watch(filterOpen, (open, wasOpen) => {
  if (wasOpen && !open) emit("query");
});

watch(
  [sentinelRef, () => props.infinite, () => props.empty, () => props.loading, () => props.finished],
  () => nextTick(bindLoadObserver),
);

watch(
  () => props.loadingMore,
  (loading, wasLoading) => {
    if (wasLoading && !loading) nextTick(bindLoadObserver);
  },
);

watch(
  () => props.pageActions.length,
  (count) => {
    document.body.classList.toggle("has-mobile-action-bar", count > 0);
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  loadObserver?.disconnect();
  document.body.classList.remove("has-mobile-action-bar");
});
</script>
