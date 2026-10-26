import { ref, watch } from "vue";

/**
 * 移动端列表累加。桌面分页仍使用原始列表，这里只在下滑时追加下一页。
 */
export function useMobileInfinite(source, options) {
  const items = ref([]);
  const page = ref(1);
  const loadingMore = ref(false);
  const finished = ref(false);
  let generation = 0;
  let retryAt = 0;

  const syncFromSource = () => {
    generation += 1;
    const rows = Array.isArray(source.value) ? [...source.value] : [];
    items.value = rows;
    page.value = 1;
    const size = options.pageSize();
    finished.value = rows.length === 0 || rows.length < size || rows.length >= options.total();
  };

  watch(source, syncFromSource, { immediate: true });

  const loadMore = async () => {
    if (loadingMore.value || finished.value || Date.now() < retryAt) return;
    if (items.value.length >= options.total()) {
      finished.value = true;
      return;
    }
    const gen = generation;
    loadingMore.value = true;
    try {
      const rows = (await options.fetchPage(page.value + 1)) || [];
      if (gen !== generation) return;
      if (!rows.length) {
        finished.value = true;
        return;
      }
      page.value += 1;
      items.value = items.value.concat(rows);
      if (rows.length < options.pageSize() || items.value.length >= options.total()) {
        finished.value = true;
      }
    } catch {
      retryAt = Date.now() + 4000;
    } finally {
      if (gen === generation) loadingMore.value = false;
    }
  };

  return { items, loadingMore, finished, loadMore };
}
