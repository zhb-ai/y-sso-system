import { ref, reactive } from 'vue'

/**
 * 搜索筛选组合式函数
 * @description 提供标准的搜索和筛选状态管理
 * @param {Object} options - 配置选项
 * @param {Object} options.defaultFilters - 默认筛选条件
 * @returns {Object} 搜索相关状态和操作方法
 */
export function useSearch(options = {}) {
  const { defaultFilters = {} } = options

  const searchKeyword = ref('')
  const filterForm = reactive({ ...defaultFilters })
  const isSearching = ref(false)

  /**
   * 设置搜索关键词
   * @param {string} keyword - 搜索关键词
   */
  const setSearchKeyword = (keyword) => {
    searchKeyword.value = keyword
  }

  /**
   * 设置筛选条件
   * @param {Object} filters - 筛选条件对象
   */
  const setFilters = (filters) => {
    Object.assign(filterForm, filters)
  }

  /**
   * 重置搜索和筛选
   * @param {Function} callback - 重置后的回调函数
   */
  const resetSearch = (callback) => {
    searchKeyword.value = ''
    Object.keys(filterForm).forEach(key => {
      filterForm[key] = defaultFilters[key] !== undefined ? defaultFilters[key] : ''
    })
    if (callback && typeof callback === 'function') {
      callback()
    }
  }

  /**
   * 执行搜索
   * @param {Function} callback - 搜索回调函数
   */
  const handleSearch = async (callback) => {
    isSearching.value = true
    try {
      if (callback && typeof callback === 'function') {
        await callback()
      }
    } finally {
      isSearching.value = false
    }
  }

  /**
   * 获取搜索参数
   * @returns {Object} 包含搜索关键词和筛选条件的对象
   */
  const getSearchParams = () => ({
    keyword: searchKeyword.value,
    ...filterForm
  })

  /**
   * 检查是否有搜索条件
   * @returns {boolean} 是否有搜索条件
   */
  const hasSearchCriteria = () => {
    return searchKeyword.value !== '' || Object.values(filterForm).some(v => v !== '' && v !== null && v !== undefined)
  }

  return {
    // 状态
    searchKeyword,
    filterForm,
    isSearching,
    // 方法
    setSearchKeyword,
    setFilters,
    resetSearch,
    handleSearch,
    getSearchParams,
    hasSearchCriteria
  }
}
