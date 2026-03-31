import { ref, reactive } from 'vue'
import { usePagination } from './usePagination'
import { useSearch } from './useSearch'

/**
 * 表格管理组合式函数
 * @description 整合分页、搜索和表格数据管理
 * @param {Object} options - 配置选项
 * @param {Function} options.fetchFn - 获取数据的异步函数
 * @param {Object} options.defaultFilters - 默认筛选条件
 * @param {number} options.defaultPageSize - 默认每页条数
 * @returns {Object} 表格相关状态和操作方法
 */
export function useTable(options = {}) {
  const {
    fetchFn,
    defaultFilters = {},
    defaultPageSize = 10
  } = options

  // 表格数据
  const data = ref([])
  const loading = ref(false)

  // 使用分页和搜索组合式函数
  const {
    currentPage,
    pageSize,
    total,
    pagination,
    resetPagination,
    setTotal,
    getPaginationParams,
    handleCurrentChange,
    handleSizeChange
  } = usePagination({ defaultPageSize })

  const {
    searchKeyword,
    filterForm,
    isSearching,
    resetSearch,
    handleSearch,
    getSearchParams,
    hasSearchCriteria
  } = useSearch({ defaultFilters })

  /**
   * 加载数据
   * @param {Object} extraParams - 额外的请求参数
   */
  const loadData = async (extraParams = {}) => {
    if (!fetchFn || typeof fetchFn !== 'function') {
      console.warn('useTable: fetchFn is required')
      return
    }

    loading.value = true
    try {
      const params = {
        ...getPaginationParams(),
        ...getSearchParams(),
        ...extraParams
      }

      const response = await fetchFn(params)
      data.value = response.data?.list || response.data || []
      setTotal(response.data?.total || response.total || 0)
    } catch (error) {
      console.error('useTable: load data failed', error)
      data.value = []
      setTotal(0)
    } finally {
      loading.value = false
    }
  }

  /**
   * 处理搜索
   */
  const onSearch = async () => {
    currentPage.value = 1
    await loadData()
  }

  /**
   * 处理重置
   */
  const onReset = async () => {
    resetSearch()
    resetPagination()
    await loadData()
  }

  /**
   * 处理页码变化
   * @param {number} page - 新页码
   */
  const onPageChange = async (page) => {
    handleCurrentChange(page, loadData)
  }

  /**
   * 处理每页条数变化
   * @param {number} size - 新的每页条数
   */
  const onSizeChange = async (size) => {
    handleSizeChange(size, loadData)
  }

  /**
   * 刷新当前页数据
   */
  const refresh = async () => {
    await loadData()
  }

  return {
    // 数据状态
    data,
    loading,
    // 分页状态
    currentPage,
    pageSize,
    total,
    pagination,
    // 搜索状态
    searchKeyword,
    filterForm,
    isSearching,
    // 方法
    loadData,
    onSearch,
    onReset,
    onPageChange,
    onSizeChange,
    refresh,
    hasSearchCriteria
  }
}
