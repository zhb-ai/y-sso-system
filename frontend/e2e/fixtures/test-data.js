/**
 * 测试数据生成工具
 * 用于生成随机测试数据
 */

/**
 * 生成随机字符串
 * @param {number} length - 字符串长度
 * @param {string} prefix - 前缀
 * @returns {string}
 */
export function generateRandomString(length = 8, prefix = '') {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let result = prefix;
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * 生成随机角色代码
 * @returns {string}
 */
export function generateRoleCode() {
  const prefixes = ['test', 'dev', 'qa', 'temp', 'auto'];
  const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
  return generateRandomString(6, `${prefix}_`);
}

/**
 * 生成随机角色名称
 * @returns {string}
 */
export function generateRoleName() {
  const prefixes = ['测试', '开发', '临时', '自动化', '演示'];
  const suffixes = ['角色', '权限组', '管理员', '操作员', '访客'];
  const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
  const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
  const randomNum = Math.floor(Math.random() * 10000);
  return `${prefix}${suffix}${randomNum}`;
}

/**
 * 生成随机角色描述
 * @returns {string}
 */
export function generateRoleDescription() {
  const descriptions = [
    '这是自动化测试生成的角色，用于测试角色管理功能',
    '临时角色，测试完成后可删除',
    '自动化测试专用角色，请勿手动修改',
    '用于验证角色CRUD操作的测试角色',
    '测试权限分配功能的示例角色'
  ];
  const desc = descriptions[Math.floor(Math.random() * descriptions.length)];
  const timestamp = new Date().toISOString();
  return `${desc} - ${timestamp}`;
}

/**
 * 生成完整的角色数据对象
 * @returns {Object}
 */
export function generateRoleData() {
  return {
    code: generateRoleCode(),
    name: generateRoleName(),
    description: generateRoleDescription()
  };
}

/**
 * 生成随机应用名称
 * @returns {string}
 */
export function generateAppName() {
  const prefixes = ['Test', 'Demo', 'Auto', 'Dev', 'Temp'];
  const suffixes = ['App', 'System', 'Platform', 'Service', 'Tool'];
  const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
  const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
  const randomNum = Math.floor(Math.random() * 10000);
  return `${prefix}${suffix}${randomNum}`;
}

/**
 * 生成随机应用代码
 * @returns {string}
 */
export function generateAppCode() {
  return generateRandomString(8, 'app_');
}

/**
 * 生成随机URL
 * @returns {string}
 */
export function generateAppUrl() {
  const domains = ['example.com', 'test.com', 'demo.com', 'app.local'];
  const domain = domains[Math.floor(Math.random() * domains.length)];
  const path = generateRandomString(5);
  return `https://${domain}/${path}`;
}

/**
 * 生成完整的应用数据对象
 * @returns {Object}
 */
export function generateAppData() {
  return {
    name: generateAppName(),
    code: generateAppCode(),
    url: generateAppUrl(),
    description: generateRoleDescription()
  };
}

/**
 * 生成随机用户名
 * @returns {string}
 */
export function generateUsername() {
  const prefixes = ['user', 'test', 'demo', 'temp'];
  const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
  return generateRandomString(6, `${prefix}_`);
}

/**
 * 生成随机姓名
 * @returns {string}
 */
export function generateDisplayName() {
  const surnames = ['张', '李', '王', '刘', '陈', '杨', '赵', '黄', '周', '吴'];
  const names = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀英', '华', '鹏'];
  const surname = surnames[Math.floor(Math.random() * surnames.length)];
  const name = names[Math.floor(Math.random() * names.length)];
  return surname + name;
}

/**
 * 生成随机邮箱
 * @param {string} username - 用户名
 * @returns {string}
 */
export function generateEmail(username) {
  const domains = ['test.com', 'example.com', 'demo.com', 'autotest.com'];
  const domain = domains[Math.floor(Math.random() * domains.length)];
  const user = username || generateRandomString(8);
  return `${user}@${domain}`;
}

/**
 * 生成随机手机号
 * @returns {string}
 */
export function generatePhone() {
  const prefixes = ['138', '139', '137', '136', '135', '134', '159', '158', '157', '150', '151', '152', '188', '187', '182', '183'];
  const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
  const suffix = Math.floor(Math.random() * 100000000).toString().padStart(8, '0');
  return prefix + suffix;
}

/**
 * 生成完整的用户数据对象
 * @returns {Object}
 */
export function generateUserData() {
  const username = generateUsername();
  return {
    username: username,
    displayName: generateDisplayName(),
    email: generateEmail(username),
    phone: generatePhone(),
    password: 'Test@123456'
  };
}
