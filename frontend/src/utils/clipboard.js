/**
 * 剪贴板工具函数
 * @description 提供复制到剪贴板的功能
 */

import { ElMessage } from 'element-plus'

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @param {Object} options - 选项
 * @param {string} options.successMessage - 成功提示消息
 * @param {string} options.errorMessage - 失败提示消息
 * @returns {Promise<boolean>} 是否复制成功
 */
export const copyToClipboard = async (text, options = {}) => {
  const {
    successMessage = '已复制到剪贴板',
    errorMessage = '复制失败，请手动复制'
  } = options

  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(successMessage)
    return true
  } catch (error) {
    console.error('Copy to clipboard failed:', error)
    ElMessage.error(errorMessage)
    return false
  }
}

/**
 * 复制文本到剪贴板（兼容旧浏览器）
 * @param {string} text - 要复制的文本
 * @returns {boolean} 是否复制成功
 */
export const copyToClipboardFallback = (text) => {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-9999px'
  textArea.style.top = '0'
  document.body.appendChild(textArea)

  try {
    textArea.focus()
    textArea.select()
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    return successful
  } catch (error) {
    console.error('Fallback copy failed:', error)
    document.body.removeChild(textArea)
    return false
  }
}

/**
 * 安全复制（优先使用现代 API，失败时使用降级方案）
 * @param {string} text - 要复制的文本
 * @param {Object} options - 选项
 * @returns {Promise<boolean>} 是否复制成功
 */
export const safeCopy = async (text, options = {}) => {
  // 优先使用现代 Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    return await copyToClipboard(text, options)
  }

  // 降级方案
  const success = copyToClipboardFallback(text)
  if (success) {
    ElMessage.success(options.successMessage || '已复制到剪贴板')
  } else {
    ElMessage.error(options.errorMessage || '复制失败，请手动复制')
  }
  return success
}
