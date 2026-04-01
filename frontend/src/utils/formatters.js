/**
 * 格式化工具函数
 * @description 提供常用的数据格式化功能
 */

/**
 * 格式化日期时间
 * @param {string|Date} dateString - 日期字符串或 Date 对象
 * @param {Object} options - 格式化选项
 * @returns {string} 格式化后的日期字符串
 */
export const formatDateTime = (dateString, options = {}) => {
  if (!dateString) return '-'

  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    ...options
  }

  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', defaultOptions)
  } catch (error) {
    console.error('formatDateTime error:', error)
    return '-'
  }
}

/**
 * 格式化日期（不含时间）
 * @param {string|Date} dateString - 日期字符串或 Date 对象
 * @returns {string} 格式化后的日期字符串
 */
export const formatDate = (dateString) => {
  return formatDateTime(dateString, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的文件大小
 */
export const formatFileSize = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 格式化数字（添加千分位分隔符）
 * @param {number} num - 数字
 * @returns {string} 格式化后的数字字符串
 */
export const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 格式化手机号（隐藏中间4位）
 * @param {string} phone - 手机号
 * @returns {string} 格式化后的手机号
 */
export const formatPhone = (phone) => {
  if (!phone) return '-'
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 格式化邮箱（隐藏部分字符）
 * @param {string} email - 邮箱地址
 * @returns {string} 格式化后的邮箱
 */
export const formatEmail = (email) => {
  if (!email) return '-'
  const [username, domain] = email.split('@')
  if (!domain) return email

  const maskedUsername = username.length > 2
    ? username.slice(0, 2) + '*'.repeat(username.length - 2)
    : '*'.repeat(username.length)

  return `${maskedUsername}@${domain}`
}

/**
 * 格式化身份证号（隐藏中间部分）
 * @param {string} idCard - 身份证号
 * @returns {string} 格式化后的身份证号
 */
export const formatIdCard = (idCard) => {
  if (!idCard) return '-'
  if (idCard.length !== 18) return idCard
  return idCard.replace(/(\d{4})\d{10}(\d{4})/, '$1**********$2')
}

/**
 * 格式化银行卡号（显示后4位）
 * @param {string} cardNo - 银行卡号
 * @returns {string} 格式化后的银行卡号
 */
export const formatBankCard = (cardNo) => {
  if (!cardNo) return '-'
  const len = cardNo.length
  if (len <= 4) return cardNo
  return '*'.repeat(len - 4) + cardNo.slice(-4)
}

/**
 * 格式化时长（秒转时分秒）
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时长
 */
export const formatDuration = (seconds) => {
  if (seconds === null || seconds === undefined) return '-'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  const parts = []
  if (hours > 0) parts.push(`${hours}小时`)
  if (minutes > 0) parts.push(`${minutes}分钟`)
  if (secs > 0 || parts.length === 0) parts.push(`${secs}秒`)

  return parts.join('')
}

/**
 * 格式化相对时间
 * @param {string|Date} dateString - 日期字符串或 Date 对象
 * @returns {string} 相对时间描述
 */
export const formatRelativeTime = (dateString) => {
  if (!dateString) return '-'

  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const month = 30 * day
  const year = 365 * day

  if (diff < minute) {
    return '刚刚'
  } else if (diff < hour) {
    return Math.floor(diff / minute) + '分钟前'
  } else if (diff < day) {
    return Math.floor(diff / hour) + '小时前'
  } else if (diff < month) {
    return Math.floor(diff / day) + '天前'
  } else if (diff < year) {
    return Math.floor(diff / month) + '个月前'
  } else {
    return Math.floor(diff / year) + '年前'
  }
}
