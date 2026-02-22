// 缓存管理模块公共常量

export const CACHE_PAGE_KEYS = {
  SUMMARY_TOTAL_FUNCTIONS: 'total_functions',
  SUMMARY_TOTAL_HITS: 'total_hits',
  SUMMARY_TOTAL_MISSES: 'total_misses',
  SUMMARY_TOTAL_HIT_RATE: 'total_hit_rate',
}

export const CACHE_FUNCTION_COLUMNS = {
  NAME: 'name',
  MODULE: 'module',
  BACKEND: 'backend',
  TTL: 'ttl',
  KEY_PREFIX: 'key_prefix',
}

export const CACHE_BACKEND_TAG_TYPE = {
  memory: 'success',
  redis: 'warning',
}

