import { ref, reactive } from 'vue'

/**
 * 对话框管理组合式函数
 * @description 提供标准的对话框状态管理和操作方法
 * @param {Object} options - 配置选项
 * @param {Object} options.defaultForm - 默认表单数据
 * @returns {Object} 对话框相关状态和操作方法
 */
export function useDialog(options = {}) {
  const { defaultForm = {} } = options

  const visible = ref(false)
  const isEditing = ref(false)
  const loading = ref(false)
  const formRef = ref(null)
  const currentItem = ref(null)

  // 表单数据
  const form = reactive({ ...defaultForm })

  /**
   * 打开新建对话框
   * @param {Object} initialData - 初始数据
   */
  const openCreateDialog = (initialData = {}) => {
    isEditing.value = false
    currentItem.value = null
    // 重置表单
    Object.keys(form).forEach(key => {
      form[key] = defaultForm[key] !== undefined ? defaultForm[key] : ''
    })
    // 合并初始数据
    Object.assign(form, initialData)
    visible.value = true
  }

  /**
   * 打开编辑对话框
   * @param {Object} item - 编辑的数据项
   * @param {Function} transformFn - 数据转换函数
   */
  const openEditDialog = (item, transformFn) => {
    isEditing.value = true
    currentItem.value = item
    // 重置表单
    Object.keys(form).forEach(key => {
      form[key] = defaultForm[key] !== undefined ? defaultForm[key] : ''
    })
    // 填充数据
    if (transformFn && typeof transformFn === 'function') {
      Object.assign(form, transformFn(item))
    } else {
      Object.assign(form, item)
    }
    visible.value = true
  }

  /**
   * 关闭对话框
   */
  const closeDialog = () => {
    visible.value = false
  }

  /**
   * 提交表单
   * @param {Function} callback - 提交回调函数
   */
  const submitForm = async (callback) => {
    if (!formRef.value) return

    try {
      await formRef.value.validate()
      loading.value = true
      if (callback && typeof callback === 'function') {
        await callback(form, isEditing.value, currentItem.value)
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置表单
   */
  const resetForm = () => {
    if (formRef.value) {
      formRef.value.resetFields()
    }
  }

  return {
    // 状态
    visible,
    isEditing,
    loading,
    formRef,
    form,
    currentItem,
    // 方法
    openCreateDialog,
    openEditDialog,
    closeDialog,
    submitForm,
    resetForm
  }
}
