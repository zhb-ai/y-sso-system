import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

/**
 * 站点信息全局 Store
 * 
 * 从后端 /settings/site 加载系统名称、描述、Logo，
 * 所有需要显示站点信息的页面从此 Store 读取。
 */
export const useSiteStore = defineStore('site', () => {
  const systemName = ref('单点登录系统')
  const systemDesc = ref('统一身份认证平台')
  const systemLogo = ref('')
  const loaded = ref(false)

  const pageTitle = computed(() => systemName.value)

  const load = async () => {
    if (loaded.value) return
    try {
      const res = await api.get('/v1/settings/site')
      if (res.data) {
        systemName.value = res.data.system_name || systemName.value
        systemDesc.value = res.data.system_desc || systemDesc.value
        systemLogo.value = res.data.system_logo || ''
      }
      loaded.value = true
    } catch {
      // 加载失败用默认值
    }
  }

  /** 更新后刷新（设置页面保存后调用） */
  const refresh = () => {
    loaded.value = false
    return load()
  }

  return {
    systemName,
    systemDesc,
    systemLogo,
    pageTitle,
    loaded,
    load,
    refresh,
  }
})
