/**
 * 测试配置文件
 * 集中管理测试环境配置、账号信息和路由配置
 */

// 基础URL配置
export const BASE_URL = 'http://localhost:5200';

// 测试账号配置
export const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

// 页面路由配置
export const ROUTES = {
  // 认证相关
  LOGIN: '/login',
  SSO_LOGIN: '/sso/login',
  
  // 主要页面
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',
  
  // 管理页面
  APPLICATIONS: '/applications',
  USERS: '/users',
  ROLES: '/roles',
  SSO_ROLES: '/sso-roles',
  ORGANIZATION: '/organization',
  EMPLOYEES: '/employees',
  SETTINGS: '/settings',
  CACHE: '/cache'
};

// 菜单名称到路由的映射（用于导航）
export const MENU_PATH_MAP = {
  '仪表盘': ROUTES.DASHBOARD,
  '应用管理': ROUTES.APPLICATIONS,
  '用户管理': ROUTES.USERS,
  '角色管理': ROUTES.ROLES,
  'SSO 角色': ROUTES.SSO_ROLES,
  '组织架构': ROUTES.ORGANIZATION,
  '员工管理': ROUTES.EMPLOYEES,
  '系统设置': ROUTES.SETTINGS,
  '缓存管理': ROUTES.CACHE,
  '个人资料': ROUTES.PROFILE
};

// 测试超时配置（毫秒）
export const TIMEOUTS = {
  DEFAULT: 5000,
  LONG: 10000,
  NAVIGATION: 3000
};

/**
 * 获取完整URL
 * @param {string} path - 路由路径
 * @returns {string} 完整URL
 */
export function getFullUrl(path) {
  return `${BASE_URL}${path}`;
}

/**
 * 根据菜单名称获取路由路径
 * @param {string} menuName - 菜单名称
 * @returns {string|null} 路由路径
 */
export function getRouteByMenuName(menuName) {
  return MENU_PATH_MAP[menuName] || null;
}
