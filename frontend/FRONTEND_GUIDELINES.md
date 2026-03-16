# 前端编码规范

## 目录

1. [设计原则](#1-设计原则)
2. [项目结构规范](#2-项目结构规范)
3. [Vue 组件规范](#3-vue-组件规范)
4. [JavaScript/TypeScript 规范](#4-javascripttypescript-规范)
5. [HTML 规范](#5-html-规范)
6. [命名规范](#6-命名规范)
7. [代码组织规范](#7-代码组织规范)
8. [性能优化规范](#8-性能优化规范)
9. [最佳实践](#9-最佳实践)
10. [代码审查规范](#10-代码审查规范)

---

## 1. 设计原则

### 1.1 核心原则
- **Ra-admin Bootstrap 风格**：严格遵循 Ra-admin 的设计语言和组件风格
- **简洁明了**：代码应简洁、清晰，避免复杂的嵌套和逻辑
- **一致性**：确保所有代码使用统一的命名规范和编码风格
- **可维护性**：代码应易于理解、修改和扩展
- **性能优先**：关注代码性能，避免不必要的渲染和计算
- **可访问性**：确保代码符合可访问性标准，支持键盘导航和屏幕阅读器

### 1.2 设计模式
- **组件化开发**：将页面拆分为独立、可复用的组件
- **单一职责原则**：每个组件和函数只负责一个功能
- **声明式编程**：优先使用声明式语法，避免命令式编程
- **响应式设计**：确保页面在不同设备上都能正常显示

---

## 2. 项目结构规范

### 2.1 标准项目结构
```
src/
├── api/                    # API 接口定义
│   ├── auth.js            # 认证相关API
│   ├── user.js            # 用户相关API
│   └── index.js           # API导出文件
├── assets/                 # 静态资源
│   ├── images/            # 图片资源
│   ├── fonts/             # 字体文件
│   └── icons/             # 图标资源
├── components/             # 通用组件
│   ├── common/            # 基础组件
│   │   ├── BaseButton.vue
│   │   ├── BaseCard.vue
│   │   └── BaseModal.vue
│   ├── layout/            # 布局组件
│   │   ├── AppHeader.vue
│   │   ├── AppSidebar.vue
│   │   └── AppFooter.vue
│   └── business/          # 业务组件
│       ├── UserProfile.vue
│       └── DataTable.vue
├── composables/            # 组合式函数
│   ├── useAuth.js         # 认证相关逻辑
│   ├── useApi.js          # API调用逻辑
│   └── useValidation.js   # 表单验证逻辑
├── layout/                 # 页面布局组件
│   ├── DefaultLayout.vue
│   ├── AuthLayout.vue
│   └── EmptyLayout.vue
├── pages/                  # 页面组件
│   ├── dashboard/         # 仪表盘页面
│   ├── auth/              # 认证页面
│   │   ├── login.vue
│   │   └── register.vue
│   └── errors/            # 错误页面
│       ├── 404.vue
│       └── 500.vue
├── router/                 # 路由配置
│   ├── index.js           # 路由主文件
│   ├── guards.js          # 路由守卫
│   └── routes.js          # 路由定义
├── stores/                 # 状态管理 (Pinia)
│   ├── auth.js            # 认证状态
│   ├── user.js            # 用户状态
│   └── app.js             # 应用状态
├── styles/                 # 样式文件
│   ├── index.css          # 主样式文件
│   ├── variables.css      # CSS变量
│   └── components/        # 组件样式
├── utils/                  # 工具函数
│   ├── date.js            # 日期处理
│   ├── validate.js        # 验证函数
│   └── format.js          # 格式化函数
├── App.vue                 # 根组件
└── main.js                 # 入口文件
```

### 2.2 文件命名规范
- **组件文件**：使用 PascalCase 命名，如 `UserProfile.vue`
- **非组件文件**：使用 camelCase 命名，如 `apiService.js`
- **页面文件**：使用 kebab-case 命名，如 `user-management.vue`
- **工具函数**：使用 camelCase 命名，如 `formatDate.js`
- **常量文件**：使用 UPPER_SNAKE_CASE 命名，如 `API_CONSTANTS.js`

---

## 3. Vue 组件规范

### 3.1 组件结构规范
- **单文件组件**：使用 `.vue` 单文件组件格式
- **结构顺序**：
  1. `<template>`：模板部分
  2. `<script setup>`：脚本部分  
  3. `<style scoped>`：样式部分
- **组件导出**：使用 `<script setup>` 语法糖，避免使用 `export default`

### 3.2 组件模板规范
- **语义化标签**：优先使用语义化 HTML5 标签
- **属性顺序**：按以下顺序排列属性：
  1. `v-if`, `v-show`, `v-for`
  2. `id`, `ref`, `key`
  3. `v-model`, `v-on`
  4. 其他指令
  5. 普通属性
- **事件命名**：使用 camelCase 命名事件，如 `@userSelect`, `@itemClick`
- **Props 传递**：明确指定 props，避免使用 `$attrs`

### 3.3 组件脚本规范
- **导入顺序**：按以下顺序导入依赖：
  1. Vue 内置 API（`ref`, `computed`, `onMounted` 等）
  2. 第三方库
  3. 项目内部组件
  4. 项目内部工具函数和 API
  5. 类型定义（TypeScript 项目）
- **响应式数据**：
  - 基本类型使用 `ref`
  - 对象类型使用 `reactive`
  - 计算属性使用 `computed`
- **函数命名**：使用 camelCase，如 `fetchData`, `handleSubmit`
- **生命周期**：按执行顺序排列生命周期钩子

### 3.4 组件样式规范
- **Scoped 样式**：优先使用 `scoped` 属性确保样式隔离
- **CSS 变量**：使用预定义的 CSS 变量
- **避免深度选择器**：尽量减少使用 `:deep()` 选择器
- **样式顺序**：按以下顺序排列样式属性：
  1. 布局属性（display, position, flex 等）
  2. 盒模型属性（width, height, margin, padding 等）
  3. 字体属性（font-size, line-height 等）
  4. 视觉属性（color, background, border 等）
  5. 其他属性

### 3.5 Element 组件使用规范
- **Button 组件**：当按钮中只有图标没有文案时，推荐使用 `circle` 类型，以获得更好的视觉效果和用户体验。
  ```vue
  <!-- 推荐用法 -->
  <el-button circle class="collapse-btn" @click="toggleCollapse">
    <el-icon>
      <component :is="isCollapse ? ArrowRight : ArrowLeft" />
    </el-icon>
  </el-button>
  ```
- **Form 组件**：当需要为表单字段添加提示信息时，推荐使用 `el-form-item` 的 `label` 插槽来实现，将提示图标与标签放在一起，提高用户体验。
  ```vue
  <!-- 推荐用法 -->
  <el-form-item>
    <template #label>
      函数名
      <el-tooltip
        content="用于筛选并查看某个缓存函数的统计与条目详情。"
        placement="top"
      >
        <el-icon class="hint-icon form-item-hint"><QuestionFilled /></el-icon>
      </el-tooltip>
    </template>
    <el-select
      v-model="selectedFunctionName"
      filterable
      clearable
      placeholder="请选择缓存函数"
      style="min-width: 260px"
    >
      <el-option
        v-for="item in functions"
        :key="item[CACHE_FUNCTION_COLUMNS.NAME]"
        :label="item[CACHE_FUNCTION_COLUMNS.NAME]"
        :value="item[CACHE_FUNCTION_COLUMNS.NAME]"
      />
    </el-select>
  </el-form-item>
  ```

### 3.6 组件示例
```vue
<template>
  <div class="user-profile">
    <header class="user-profile__header">
      <h2>{{ user.name }}</h2>
      <BaseButton 
        variant="primary" 
        size="small"
        @click="handleEdit"
      >
        编辑资料
      </BaseButton>
    </header>
    
    <main class="user-profile__content">
      <BaseCard>
        <template #header>
          <h3>基本信息</h3>
        </template>
        
        <UserInfo :user="user" />
      </BaseCard>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { userApi } from '@/api'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import UserInfo from '@/components/business/UserInfo.vue'

// Props 定义
const props = defineProps({
  userId: {
    type: String,
    required: true
  }
})

// Emits 定义
const emit = defineEmits(['edit', 'update'])

// 状态管理
const authStore = useAuthStore()
const user = ref(null)
const loading = ref(false)

// 计算属性
const canEdit = computed(() => {
  return authStore.user?.id === props.userId
})

// 生命周期钩子
onMounted(async () => {
  await fetchUser()
})

// 方法定义
const fetchUser = async () => {
  loading.value = true
  try {
    const response = await userApi.getUser(props.userId)
    user.value = response.data
  } catch (error) {
    console.error('获取用户信息失败:', error)
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  emit('edit', user.value)
}
</script>

<style scoped>
.user-profile {
  padding: var(--spacing-lg);
}

.user-profile__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.user-profile__content {
  display: grid;
  gap: var(--spacing-md);
}
</style>
```

---

## 4. JavaScript/TypeScript 规范

### 4.1 基本语法规范
- **使用 ES6+ 语法**：优先使用现代 JavaScript 语法
- **分号使用**：始终使用分号结束语句
- **引号使用**：使用单引号 `'` 或反引号 `` ` ``，避免使用双引号 `"`
- **缩进**：使用 2 个空格进行缩进
- **括号使用**：在 `if`, `for`, `while` 等语句中始终使用括号

### 4.2 变量和常量规范
- **变量声明**：使用 `const` 或 `let`，避免使用 `var`
- **优先使用 `const`**：仅在需要重新赋值时使用 `let`
- **命名规范**：
  - 变量和函数：camelCase，如 `userName`, `fetchData`
  - 常量：UPPER_SNAKE_CASE，如 `API_BASE_URL`
  - 类和构造函数：PascalCase，如 `UserService`
- **布尔值变量**：使用 `is/has/can` 前缀，如 `isActive`, `hasPermission`

### 4.3 函数规范
- **函数长度**：函数应保持简洁，尽量控制在 50 行以内
- **参数数量**：函数参数不超过 5 个，超过时使用对象参数
- **默认参数**：使用默认参数语法，避免在函数体内判断
- **返回值**：函数应明确返回值，避免隐式返回 `undefined`
- **异步函数**：使用 `async/await` 处理异步操作

### 4.4 错误处理规范
- **try/catch 使用**：对可能出错的异步操作使用 try/catch
- **错误信息**：提供清晰的错误信息，便于调试
- **错误类型**：区分不同类型的错误，使用适当的错误处理策略
- **日志记录**：使用适当的日志级别记录错误信息

### 4.5 代码示例
```javascript
// 常量定义
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
const MAX_RETRY_COUNT = 3
const CACHE_EXPIRY_TIME = 5 * 60 * 1000 // 5分钟

// 函数定义
const fetchUserData = async (userId, options = {}) => {
  const { includeProfile = true, cache = true } = options
  
  // 参数验证
  if (!userId || typeof userId !== 'string') {
    throw new Error('Invalid userId parameter')
  }
  
  try {
    // 构建请求配置
    const config = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      params: { includeProfile }
    }
    
    // 发送请求
    const response = await apiClient.get(`/users/${userId}`, config)
    
    // 缓存处理
    if (cache) {
      cacheUserData(userId, response.data)
    }
    
    return response.data
  } catch (error) {
    // 错误处理
    console.error('Failed to fetch user data:', error)
    
    if (error.response?.status === 404) {
      throw new Error('User not found')
    }
    
    throw new Error('Failed to fetch user data')
  }
}

// 箭头函数
const formatDate = (dateString, format = 'YYYY-MM-DD') => {
  if (!dateString) return '-'
  
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  
  return date.toLocaleDateString('zh-CN')
}
```

---

## 5. HTML 规范

### 5.1 基础语法规范
- **HTML5 语法**：使用标准的 HTML5 语法
- **标签名**：使用小写字母
- **属性名**：使用小写字母
- **属性值**：使用双引号包裹属性值
- **自闭合标签**：正确关闭自闭合标签，如 `<br />`, `<img />`

### 5.2 语义化标签规范
- **优先使用语义化标签**：如 `<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`
- **避免过度使用 `<div>`**：根据内容语义选择合适的标签
- **表单元素**：使用适当的表单标签和属性
- **结构化内容**：使用合适的标签表示内容层次结构

### 5.3 可访问性规范
- **图片标签**：为所有图片添加 `alt` 属性
- **表单标签**：确保表单元素有对应的 `<label>` 标签
- **ARIA 属性**：使用 `aria-*` 属性增强可访问性
- **键盘导航**：确保所有交互元素支持键盘操作
- **颜色对比**：确保文本与背景有足够的颜色对比度

### 5.4 HTML 示例
```html
<!-- 正确的语义化结构 -->
<article class="blog-post">
  <header class="blog-post__header">
    <h1>文章标题</h1>
    <time datetime="2024-01-01">2024年1月1日</time>
  </header>
  
  <main class="blog-post__content">
    <p>文章内容...</p>
    
    <figure class="blog-post__image">
      <img src="image.jpg" alt="描述图片内容的文字">
      <figcaption>图片说明文字</figcaption>
    </figure>
  </main>
  
  <footer class="blog-post__footer">
    <nav class="blog-post__nav">
      <a href="/previous" rel="prev">上一篇文章</a>
      <a href="/next" rel="next">下一篇文章</a>
    </nav>
  </footer>
</article>

<!-- 正确的表单结构 -->
<form class="contact-form" @submit.prevent="handleSubmit">
  <div class="form-group">
    <label for="email" class="form-label">邮箱地址</label>
    <input 
      id="email"
      v-model="form.email"
      type="email"
      class="form-control"
      required
      aria-describedby="email-help"
    >
    <div id="email-help" class="form-text">我们不会分享您的邮箱地址</div>
  </div>
  
  <button type="submit" class="btn btn-primary" :disabled="loading">
    提交表单
  </button>
</form>
```

---

## 6. 命名规范

### 6.1 变量命名规范
- **camelCase**：变量和函数使用 camelCase，如 `userName`, `getUserData`
- **UPPER_SNAKE_CASE**：常量使用大写蛇形命名，如 `API_URL`, `MAX_COUNT`
- **PascalCase**：类和构造函数使用 PascalCase，如 `UserService`, `DataModel`
- **kebab-case**：文件名和 CSS 类名使用 kebab-case，如 `user-profile.vue`, `.user-profile`

### 6.2 布尔值变量命名
- **is 前缀**：表示状态，如 `isLoading`, `isVisible`
- **has 前缀**：表示拥有，如 `hasPermission`, `hasError`
- **can 前缀**：表示能力，如 `canEdit`, `canDelete`
- **should 前缀**：表示应该，如 `shouldShow`, `shouldValidate`

### 6.3 函数命名规范
- **动词开头**：函数名应以动词开头，如 `getUser`, `updateProfile`
- **描述性**：名称应清晰表达函数的功能
- **一致性**：相同功能的函数保持命名一致性
- **避免缩写**：除非是广泛认可的缩写

### 6.4 组件命名规范
- **PascalCase**：组件名使用 PascalCase，如 `UserProfile`, `DataTable`
- **语义化**：名称应清晰反映组件的功能
- **避免通用名称**：避免使用过于通用的名称，如 `Component`, `Item`
- **业务相关**：名称应与业务功能相关联

---

## 7. 代码组织规范

### 7.1 导入顺序规范
按以下顺序组织导入语句：
1. **Vue 内置 API**：如 `ref`, `computed`, `onMounted`
2. **第三方库**：如 `axios`, `dayjs`
3. **内部组件**：项目内部的 Vue 组件
4. **内部工具函数**：项目内部的工具函数
5. **API 服务**：项目内部的 API 服务
6. **状态管理**：Pinia store 等
7. **类型定义**：TypeScript 类型定义

### 7.2 代码块组织顺序
在 `<script setup>` 中按以下顺序组织代码：
1. **导入语句**
2. **Props 定义**
3. **Emits 定义**
4. **状态变量定义**
5. **计算属性**
6. **监听器**
7. **生命周期钩子**
8. **方法定义**
9. **工具函数**

### 7.3 注释规范
- **文件注释**：在文件开头说明文件用途
- **函数注释**：为复杂函数添加 JSDoc 注释
- **业务逻辑注释**：为复杂的业务逻辑添加注释
- **TODO 注释**：标记需要后续处理的内容
- **FIXME 注释**：标记需要修复的问题

### 7.4 代码组织示例
```vue
<script setup>
/**
 * 用户资料组件
 * 
 * 用于显示和编辑用户基本信息，包括头像、姓名、邮箱等。
 * 支持编辑模式和只读模式切换。
 */

// 1. Vue 内置 API
import { ref, computed, onMounted, watch } from 'vue'

// 2. 第三方库
import { useVuelidate } from '@vuelidate/core'
import { required, email } from '@vuelidate/validators'

// 3. 内部组件
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import AvatarUpload from '@/components/common/AvatarUpload.vue'

// 4. 内部工具函数
import { formatDate, validatePhone } from '@/utils/format'
import { showToast, showConfirm } from '@/utils/message'

// 5. API 服务
import { userApi } from '@/api'

// 6. 状态管理
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'

// Props 定义
const props = defineProps({
  userId: {
    type: String,
    required: true
  },
  editable: {
    type: Boolean,
    default: false
  }
})

// Emits 定义
const emit = defineEmits(['update', 'error'])

// 状态变量
const loading = ref(false)
const user = ref(null)
const isEditing = ref(false)
const form = ref({
  name: '',
  email: '',
  phone: ''
})

// 计算属性
const canEdit = computed(() => {
  return props.editable && authStore.hasPermission('user:update')
})

const isFormValid = computed(() => {
  return form.value.name && form.value.email
})

// 生命周期钩子
onMounted(async () => {
  await loadUserData()
})

// 监听器
watch(() => props.userId, async (newId) => {
  if (newId) {
    await loadUserData()
  }
})

// 方法定义
const loadUserData = async () => {
  loading.value = true
  try {
    const response = await userApi.getUser(props.userId)
    user.value = response.data
    form.value = { ...response.data }
  } catch (error) {
    console.error('加载用户数据失败:', error)
    emit('error', error)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (!isFormValid.value) {
    showToast('请填写完整信息', 'warning')
    return
  }
  
  const confirmed = await showConfirm('确定要保存修改吗？')
  if (!confirmed) return
  
  loading.value = true
  try {
    await userApi.updateUser(props.userId, form.value)
    showToast('保存成功', 'success')
    emit('update', form.value)
    isEditing.value = false
  } catch (error) {
    console.error('保存用户数据失败:', error)
    showToast('保存失败，请重试', 'error')
  } finally {
    loading.value = false
  }
}
</script>
```

---

## 8. 性能优化规范

### 8.1 组件性能优化
- **v-if vs v-show**：根据使用场景选择合适的指令
- **v-for 使用**：为列表项添加唯一的 `key` 属性
- **计算属性**：使用 `computed` 缓存复杂计算结果
- **watch 使用**：避免深度监听大型对象
- **组件懒加载**：使用 `defineAsyncComponent` 进行组件懒加载

### 8.2 渲染优化
- **避免不必要的重新渲染**：使用 `v-memo` 优化列表渲染
- **虚拟滚动**：对于大型列表使用虚拟滚动
- **防抖节流**：对频繁触发的事件使用防抖或节流
- **图片优化**：使用适当的图片格式和大小
- **代码分割**：使用动态导入进行代码分割

### 8.3 网络优化
- **请求合并**：合并多个相同的请求
- **缓存策略**：合理使用本地缓存
- **数据预加载**：预加载可能需要的数据
- **错误重试**：实现请求失败的重试机制
- **加载状态**：为异步操作提供加载状态反馈

### 8.4 性能优化示例
```vue
<template>
  <!-- 使用 v-memo 优化列表渲染 -->
  <div v-for="item in filteredList" :key="item.id" v-memo="[item.status]">
    <ListItem :item="item" />
  </div>
  
  <!-- 使用计算属性避免重复计算 -->
  <div>{{ formattedData }}</div>
  
  <!-- 异步组件懒加载 -->
  <AsyncComponent v-if="showModal" />
</template>

<script setup>
import { computed, ref, defineAsyncComponent } from 'vue'
import { debounce } from '@/utils/performance'

// 异步组件懒加载
const AsyncComponent = defineAsyncComponent(() => 
  import('@/components/ComplexComponent.vue')
)

// 计算属性缓存
const formattedData = computed(() => {
  return expensiveCalculation(props.data)
})

// 防抖函数
const handleSearch = debounce((query) => {
  performSearch(query)
}, 300)

// 虚拟滚动优化大型列表
const VirtualList = defineAsyncComponent(() => 
  import('@/components/VirtualList.vue')
)
</script>
```

---

## 9. 最佳实践

### 9.1 开发工具使用
- **编辑器配置**：使用 VS Code 并配置合适的插件
- **代码格式化**：使用 Prettier 统一代码格式
- **代码检查**：使用 ESLint 检查代码质量
- **Git 使用**：遵循 Git 最佳实践和提交规范
- **调试工具**：熟练使用浏览器开发者工具

### 9.2 代码复用
- **组件抽象**：将通用功能抽象为可复用组件
- **组合式函数**：使用 Composables 复用逻辑
- **工具函数**：将通用功能封装为工具函数
- **配置提取**：将可配置项提取到配置文件中
- **模板提取**：将重复使用的模板提取为独立组件

### 9.3 团队协作
- **代码审查**：进行代码审查确保代码质量
- **文档编写**：为复杂功能编写清晰的文档
- **知识分享**：定期进行技术分享和讨论
- **规范遵循**：严格遵循团队制定的编码规范
- **沟通协作**：保持良好的沟通和协作习惯

### 9.4 持续改进
- **代码重构**：定期重构代码以提高质量
- **性能监控**：监控应用性能并及时优化
- **技术更新**：关注技术发展趋势并适时更新
- **最佳实践**：学习和应用行业最佳实践
- **反馈收集**：收集用户反馈并持续改进

---

## 10. 代码审查规范

### 10.1 审查要点
- **代码规范**：检查是否符合编码规范
- **功能实现**：验证是否正确实现了需求
- **性能考虑**：检查是否存在性能问题
- **安全性**：检查是否存在安全漏洞
- **可测试性**：代码是否易于测试
- **可维护性**：代码是否易于理解和维护

### 10.2 审查流程
1. **自评**：开发者先自行检查代码
2. **提交审查**：创建合并请求并描述变更
3. **同行审查**：至少一名团队成员进行审查
4. **反馈处理**：根据审查意见修改代码
5. **最终确认**：审查者确认修改并批准合并

### 10.3 审查标准
- **功能性**：代码是否正确实现了预期功能
- **可读性**：代码是否易于阅读和理解
- **可维护性**：代码是否易于修改和扩展
- **性能**：代码是否高效，没有明显性能问题
- **安全性**：代码是否考虑了安全性问题
- **测试覆盖**：是否有足够的测试用例

---

## 总结

本编码规范基于 Vue 3 和现代化前端开发最佳实践，旨在确保项目代码的一致性、可维护性和性能。所有开发人员必须严格遵循本规范，确保：

1. **代码质量**：所有代码符合统一的编码标准
2. **团队协作**：规范化的代码便于团队协作
3. **可维护性**：代码易于理解、修改和扩展
4. **性能优化**：关注代码性能，避免不必要的开销
5. **最佳实践**：遵循行业最佳实践和标准

随着项目的发展和技术的变化，本规范将定期更新和完善。如有疑问或建议，请及时与团队沟通。