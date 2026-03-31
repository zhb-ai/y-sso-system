import { reactive, ref } from 'vue'

/**
 * 分页组合式函数
 * @description 提供标准的分页状态管理和操作方法
 * @param {Object} options - 配置选项
 * @param {number} options.defaultPageSize - 默认每页条数，默认 10
 * @param {number[]} options.pageSizes - 可选的每页条数数组，默认 [10, 20, 50, 100]
 * @returns {Object} 分页相关状态和操作方法
 */
export function usePagination(options = {}) {
  const {
    defaultPageSize = 10,
    pageSizes = [10, 20, 50, 100]
  } = options

  const currentPage = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)
  const loading = ref(false)

  const pagination = reactive({
    currentPage,
    pageSize,
    total,
    pageSizes
  })

  /**
   * 重置分页到初始状态
   */
  const resetPagination = () => {
    currentPage.value = 1
    pageSize.value = defaultPageSize
    total.value = 0
  }

  /**
   * 设置总条数
   * @param {number} value - 总条数
   */
   const setTotal = (value) => {
    total.value = value
  }

  /**
   * 获取当前分页参数
   * @returns {Object} 包含 page 和 pageSize 的对象
   */
  const getPaginationParams = () => ({
    page: currentPage.value,
    pageSize: pageSize.value
  })

  /**
   * 处理页码变化
   * @param {number} page - 新页码
   * @param {Function} callback - 页码变化后的回调函数
   */
  const handleCurrentChange = (page, callback) => {
    currentPage.value = page
    if (callback && typeof callback === 'function') {
      callback()
    }
  }

  /**
   * 处理每页条数变化
   * @param {number} size - 新的每页条数
   * @param {Function} callback - 条数变化后的回调函数
   */
  const handleSizeChange = (size, callback) => {
    pageSize.value = size
    currentPage.value = 1 // 重置到第一页
    if (callback && typeof callback === 'function') {
      callback()
    }
  }

  return {
    // 状态
    currentPage,
    pageSize,
    total,
    loading,
    pagination,
    // 方法
    resetPagination,
    setTotal,
    getPaginationParams,
    handleCurrentChange,
    handleSizeChange
  }
}
