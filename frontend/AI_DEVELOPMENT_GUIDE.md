# AI编程助手前端开发规范文档

## 📋 文档说明
本规范用于指导AI编程助手在开发前端代码时的标准化操作，确保代码一致性、可维护性和符合项目整体架构。

---

## 🏗️ 1. 文件结构规范

### 1.1 目录结构
```
src/
├── api/                    # API接口定义
├── assets/                 # 静态资源
├── components/             # 通用组件
│   ├── common/            # 基础组件
│   ├── layout/            # 布局组件
│   └── business/          # 业务组件
├── composables/            # 组合式函数 存放封装好的逻辑脚本
├── pages/                  # 页面组件（核心目录）
├── styles/                 # 样式文件（核心目录）
├── utils/                  # 工具函数
└── stores/                 # 状态管理
```

### 1.2 文件放置规则
| 文件类型 | 放置位置 | 命名规范 | 示例 |
|---------|---------|----------|------|
| 页面文件 | `pages/业务目录/` | kebab-case | `user-create.vue` |
| 通用组件 | `components/common/` | PascalCase | `BaseButton.vue` |
| 业务组件 | `components/business/` | PascalCase | `UserProfile.vue` |
| 样式文件 | `styles/对应分类/` | kebab-case | `buttons.css` |
| 工具函数 | `utils/` | camelCase | `formatDate.js` |

---

## 📝 2. Vue组件编写规范

### 2.1 组件结构模板
```vue
<template>
  <!-- 语义化HTML标签优先 -->
  <div class="组件名">
    <!-- 内容区域 -->
  </div>
</template>

<script setup>
// 1. Vue内置API
import { ref, computed, onMounted } from 'vue'

// 2. 第三方库
import { ElMessage } from 'element-plus'

// 3. 内部组件
import BaseButton from '@/components/common/BaseButton.vue'

// 4. 工具函数和API
import { userApi } from '@/api'
import { formatDate } from '@/utils/format'

// 5. 状态管理
import { useAuthStore } from '@/stores/auth'

// Props定义（必须）
const props = defineProps({
  // 明确定义每个prop的类型和验证
})

// Emits定义（必须）
const emit = defineEmits(['success', 'error'])

// 状态变量
const loading = ref(false)
const data = ref(null)

// 计算属性
const isValid = computed(() => {
  return data.value && data.value.length > 0
})

// 生命周期
onMounted(() => {
  fetchData()
})

// 方法定义
const fetchData = async () => {
  loading.value = true
  try {
    const response = await userApi.getList()
    data.value = response.data
  } catch (error) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}
</script>

<!-- 样式部分：尽量省略 -->
<style scoped>
/* 仅当必须时添加，且使用CSS变量 */
.组件名 {
  padding: var(--spacing-lg);
}
</style>
```

### 2.2 组件编写原则
- ✅ **必须**使用`<script setup>`语法
- ✅ **必须**定义props和emits
- ✅ **必须**使用语义化HTML标签
- ✅ **必须**使用CSS变量
- ❌ **禁止**在页面组件中添加样式
- ❌ **禁止**使用内联样式（除动态样式外）

---

## 🎨 3. 样式管理规范

### 3.1 样式使用优先级
1. **第一优先**：使用CSS变量和公共类名
2. **第二优先**：使用Element Plus组件样式
3. **第三优先**：在`styles/`目录中添加样式文件
4. **第四优先**：如果没有合适的样式，需要考虑样式是否为共性样式，是否可以提取到`styles/base/`目录中，创建新的公共样式
5. **最后选择**：如果只有本页面才有的及其他属性的样式，才考虑在组件内使用scoped样式，应尽量避免

### 3.2 CSS变量使用
```css
/* 颜色变量 */
color: var(--primary);
background-color: var(--light-gray);

/* 间距变量 */
margin: var(--spacing-md);
padding: var(--card-padding);

/* 字体变量 */
font-size: var(--font-size-lg);
line-height: var(--line-height);
```

### 3.3 BEM命名规范
```css
/* Block（块） */
.user-card {}

/* Element（元素） */
.user-card__header {}
.user-card__content {}

/* Modifier（修饰符） */
.user-card--primary {}
.user-card--large {}
```

### 3.4 样式文件结构
```
styles/
├── base/                  # 基础样式
│   ├── variables.css      # CSS变量
│   ├── reset.css         # 样式重置
│   └── typography.css    # 字体排版
├── components/           # 组件样式
│   ├── ui/              # UI组件样式
│   └── custom/          # 自定义组件样式
├── pages/               # 页面特定样式
└── utilities/           # 工具类样式
```

---

## 🔧 4. 代码组织规范

### 4.1 导入顺序（必须遵守）
```javascript
// 1. Vue内置API
import { ref, computed, watch, onMounted } from 'vue'

// 2. 第三方库
import { ElMessage, ElLoading } from 'element-plus'

// 3. 内部组件
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'

// 4. 工具函数和API
import { userApi } from '@/api'
import { formatDate, validatePhone } from '@/utils/format'

// 5. 状态管理
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
```

### 4.2 代码块组织顺序
```javascript
// 1. Props定义
const props = defineProps({...})

// 2. Emits定义
const emit = defineEmits([...])

// 3. 状态变量
const loading = ref(false)
const data = ref(null)

// 4. 计算属性
const isValid = computed(() => {...})

// 5. 监听器
watch(data, (newVal) => {...})

// 6. 生命周期钩子
onMounted(() => {...})

// 7. 方法定义
const handleSubmit = async () => {...}
```

---

## 🚫 5. 禁止事项

### 5.1 样式相关禁止
- ❌ **禁止**在页面文件中添加大量CSS样式
- ❌ **禁止**使用内联样式（除动态样式外）
- ❌ **禁止**使用硬编码颜色值、尺寸值
- ❌ **禁止**创建重复的样式定义
- ❌ **禁止**使用`!important`（极端情况除外）

### 5.2 代码结构禁止
- ❌ **禁止**违反导入顺序
- ❌ **禁止**在组件中混合业务逻辑和UI逻辑
- ❌ **禁止**创建重复的工具函数
- ❌ **禁止**使用非语义化HTML标签

### 5.3 命名规范禁止
- ❌ **禁止**混用命名规范（如`userName`和`user-name`混用）
- ❌ **禁止**使用过于通用的名称（如`data`、`item`、`component`）
- ❌ **禁止**使用缩写（除非是广泛认可的缩写）

---

## ✅ 6. 最佳实践检查清单

### 6.1 组件开发检查
- [ ] 是否使用了`<script setup>`语法？
- [ ] 是否明确定义了props和emits？
- [ ] 是否使用了语义化HTML标签？
- [ ] 是否遵循了导入顺序？
- [ ] 是否使用了CSS变量？
- [ ] 是否保持了组件样式最小化？

### 6.2 样式使用检查
- [ ] 是否优先使用了公共样式？
- [ ] 是否使用了CSS变量？
- [ ] 是否遵循了BEM命名规范？
- [ ] 是否避免了内联样式？
- [ ] 是否保持了样式文件结构清晰？

### 6.3 代码质量检查
- [ ] 是否遵循了命名规范？
- [ ] 是否保持了代码简洁？
- [ ] 是否添加了必要的注释？
- [ ] 是否处理了错误情况？
- [ ] 是否考虑了可访问性？

---

## 📚 7. 快速参考

### 7.1 常用CSS变量
```css
/* 颜色 */
--primary: 72, 190, 206
--success: 174, 204, 52
--danger: 229, 94, 64

/* 间距 */
--spacing-xs: 0.25rem
--spacing-sm: 0.5rem
--spacing-md: 1rem
--spacing-lg: 1.5rem

/* 字体 */
--font-size: 14px
--font-size-sm: 12px
--font-size-lg: 16px
```

### 7.2 常用类名
```html
<!-- 布局类 -->
<div class="container">
<div class="card">
<div class="form-group">

<!-- 按钮类 -->
<button class="btn btn-primary">
<button class="btn btn-secondary">

<!-- 文本类 -->
<span class="text-primary">
<span class="text-danger">
```

### 7.3 错误处理模板
```javascript
try {
  const response = await apiCall()
  // 处理成功响应
} catch (error) {
  ElMessage.error(getErrorMessage(error, '操作失败'))
} finally {
  loading.value = false
}
```

---

## 🎯 总结

本规范的核心原则：**简洁、一致、可维护**

1. **页面文件专注逻辑**，样式最小化
2. **优先使用公共资源**，避免重复造轮子
3. **严格遵循命名和组织规范**
4. **保持代码清晰和可维护性**

AI编程助手在生成代码时，必须严格遵循本规范，确保生成的代码与项目现有代码保持一致性和高质量。