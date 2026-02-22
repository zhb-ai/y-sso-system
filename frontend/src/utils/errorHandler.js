import { ElMessage } from 'element-plus'

/**
 * 处理API错误并显示适当的错误消息
 * @param {Error} error - 错误对象
 * @param {string} defaultMessage - 默认错误消息
 * @param {Object} options - 选项
 * @param {boolean} options.showMessage - 是否显示错误消息，默认为true
 * @param {Function} options.customHandler - 自定义错误处理函数
 * @returns {string} 错误消息
 */
export const handleApiError = (error, defaultMessage = '操作失败，请稍后重试', options = {}) => {
  const { showMessage = true, customHandler } = options
  
  let errorMessage = defaultMessage
  
  // 如果有自定义错误处理函数，优先使用
  if (customHandler && typeof customHandler === 'function') {
    const customResult = customHandler(error)
    if (customResult) {
      errorMessage = customResult
    }
  } else {
    // 根据错误类型确定错误消息
    if (error.isTimeoutError) {
      errorMessage = '请求超时，请检查网络连接后重试'
    } else if (error.isNetworkError) {
      errorMessage = '网络连接失败，请检查网络设置或联系管理员'
    } else if (error.message) {
      errorMessage = error.message
    }
  }
  
  // 显示错误消息
  if (showMessage) {
    ElMessage.error(errorMessage)
  }
  
  // 在控制台记录详细错误
  console.error('API错误:', error)
  
  return errorMessage
}

/**
 * 创建API调用的错误处理包装器
 * @param {Function} apiCall - API调用函数
 * @param {string} errorMessage - 默认错误消息
 * @param {Object} options - 选项
 * @returns {Promise} 包装后的API调用
 */
export const withErrorHandling = async (apiCall, errorMessage = '操作失败，请稍后重试', options = {}) => {
  try {
    return await apiCall()
  } catch (error) {
    handleApiError(error, errorMessage, options)
    throw error
  }
}

/**
 * 根据操作类型生成默认错误消息
 * @param {string} operation - 操作类型
 * @returns {string} 错误消息
 */
export const getDefaultErrorMessage = (operation) => {
  const errorMessages = {
    create: `创建失败，请稍后重试`,
    update: `更新失败，请稍后重试`,
    delete: `删除失败，请稍后重试`,
    get: `获取数据失败，请稍后重试`,
    save: `保存失败，请稍后重试`,
    reset: `重置失败，请稍后重试`,
    login: `登录失败，请稍后重试`,
    logout: `退出登录失败，请稍后重试`,
    upload: `上传失败，请稍后重试`,
    download: `下载失败，请稍后重试`
  }
  
  return errorMessages[operation] || '操作失败，请稍后重试'
}