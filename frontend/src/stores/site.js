import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

const DEFAULT_SYSTEM_NAME = '单点登录系统'
const DEFAULT_SYSTEM_DESC = '统一身份认证平台'
const SITE_CACHE_KEY = 'site_settings_cache'

function readSiteCache() {
  try {
    const raw = localStorage.getItem(SITE_CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    const cache = {
      systemName: parsed?.systemName || parsed?.system_name || '',
      systemDesc: parsed?.systemDesc || parsed?.system_desc || '',
      systemLogo: parsed?.systemLogo || parsed?.system_logo || '',
    }
    // 轻量迁移：把旧字段名写回为统一格式
    writeSiteCache(cache)
    return cache
  } catch {
    return null
  }
}

function writeSiteCache({ systemName, systemDesc, systemLogo }) {
  try {
    localStorage.setItem(
      SITE_CACHE_KEY,
      JSON.stringify({
        systemName: systemName || '',
        systemDesc: systemDesc || '',
        systemLogo: systemLogo || '',
      })
    )
  } catch {
    // 忽略本地缓存写入异常（如隐私模式/存储空间不足）
  }
}

/**
 * 站点信息全局 Store
 * 
 * 从后端 /settings/site 加载系统名称、描述、Logo，
 * 所有需要显示站点信息的页面从此 Store 读取。
 */
export const useSiteStore = defineStore('site', () => {
  const cached = readSiteCache()
  const systemName = ref(cached?.systemName || DEFAULT_SYSTEM_NAME)
  const systemDesc = ref(cached?.systemDesc || DEFAULT_SYSTEM_DESC)
  const systemLogo = ref(cached?.systemLogo || '')
  const loaded = ref(false)

  const pageTitle = computed(() => systemName.value)

  const load = async () => {
    if (loaded.value) return
    try {
      const res = await api.get('/v1/settings/site')
      if (res.data) {
        systemName.value = res.data.system_name || systemName.value || DEFAULT_SYSTEM_NAME
        systemDesc.value = res.data.system_desc || systemDesc.value || DEFAULT_SYSTEM_DESC
        systemLogo.value = res.data.system_logo || systemLogo.value || ''
        writeSiteCache({
          systemName: systemName.value,
          systemDesc: systemDesc.value,
          systemLogo: systemLogo.value,
        })
      }
      loaded.value = true
    } catch {
      // 加载失败用默认值
      loaded.value = false
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
