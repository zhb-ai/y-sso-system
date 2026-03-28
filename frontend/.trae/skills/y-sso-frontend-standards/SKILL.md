---
name: "y-sso-frontend-standards"
description: "强制遵循Y-SSO前端开发规范：Vue组件规范、CSS变量使用、BEM命名、导入顺序、文件结构等。仅在修改 frontend/src/ 目录下文件时调用。"
---

# Y-SSO 前端开发规范

## 调用条件

**必须调用此技能当：**
- 用户要求修改 `d:\www\web\aicode\y-sso-system\frontend\src\` 目录下的任何文件
- 涉及 Vue 组件开发、样式修改、JavaScript/TypeScript 代码编写
- 创建新的页面、组件、工具函数或样式文件
- 重构或优化现有前端代码

**建议调用此技能当：**
- 进行前端代码审查
- 处理与项目架构相关的任务

---

## 1. 项目结构规范

### 1.1 目录结构
```
src/
├── api/                    # API接口定义
├── assets/                 # 静态资源
├── components/             # 通用组件
│   ├── common/            # 基础组件 (BaseButton.vue)
│   ├── layout/            # 布局组件 (AppHeader.vue)
│   └── business/          # 业务组件 (UserProfile.vue)
├── pages/                  # 页面组件（核心目录）
├── styles/                 # 样式文件（核心目录）
│   ├── base/              # 基础样式 (variables.css)
│   ├── components/        # 组件样式
│   ├── layout/            # 布局样式
│   ├── pages/             # 页面样式
│   └── utilities/         # 工具类
├── utils/                  # 工具函数
└── stores/                 # 状态管理
```

### 1.2 文件命名规范
| 文件类型 | 放置位置 | 命名规范 | 示例 |
|---------|---------|----------|------|
| 页面文件 | `pages/业务目录/` | kebab-case | `user-create.vue` |
| 通用组件 | `components/common/` | PascalCase | `BaseButton.vue` |
| 业务组件 | `components/business/` | PascalCase | `UserProfile.vue` |
| 样式文件 | `styles/对应分类/` | kebab-case | `buttons.css` |
| 工具函数 | `utils/` | camelCase | `formatDate.js` |

---

## 2. Vue 组件编写规范

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

## 3. 样式管理规范

### 3.1 样式使用优先级
1. **第一优先**：使用CSS变量和公共类名
2. **第二优先**：使用Element Plus组件样式
3. **第三优先**：在`styles/`目录中添加样式文件
4. **第四优先**：如果没有合适的样式，需要考虑样式是否为共性样式，是否可以提取到`styles/base/`目录中，创建新的公共样式
5. **最后选择**：如果只有本页面才有的及其他属性的样式，才考虑在组件内使用scoped样式，应尽量避免

### 3.2 CSS变量使用（强制）
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

### 3.3 标准CSS变量定义
```css
:root {
  /* 主色调 */
  --primary: 72, 190, 206;
  --secondary: 139, 132, 118;
  --success: 174, 204, 52;
  --danger: 229, 94, 64;
  --warning: 235, 195, 63;
  --info: 83, 90, 231;
  
  /* 中性色 */
  --light: 229, 227, 224;
  --dark: 72, 68, 61;
  --white: #ffffff;
  
  /* 背景色 */
  --bodybg-color: #f9f9f9;
  --light-gray: #f4f7f8;
  
  /* 间距 */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* 组件间距 */
  --card-padding: 1.5rem;
  --section-margin: 1.5rem;
}
```

### 3.4 字体变量规范（强制）
**必须使用预定义的字体变量，禁止硬编码字体大小和字重**

#### 字体大小变量（5档规范）
| 变量名 | 值 | 使用场景 |
|-------|-----|---------|
| `--el-font-size-xxl` | 22px | 大标题、数字展示 |
| `--el-font-size-xl` | 20px | 页面主标题 |
| `--el-font-size-lg` | 18px | 卡片标题、重要信息 |
| `--el-font-size-md` | 16px | 小标题、强调文本 |
| `--el-font-size-base` | 14px | 正文、默认文本 |
| `--el-font-size-sm` | 13px | 辅助文本、描述信息 |
| `--el-font-size-xs` | 12px | 标签、提示信息 |

#### 字重变量
| 变量名 | 值 | 使用场景 |
|-------|-----|---------|
| `--el-font-weight-extra-bold` | 600 | 标题、强调 |
| `--el-font-weight-bold` | 500 | 半粗体、标签 |
| `--el-font-weight-medium` | 400 | 正常文本 |
| `--el-font-weight-regular` | 300 | 轻量文本 |

#### 行高变量（5档规范）
| 变量名 | 值 | 使用场景 |
|-------|-----|---------|
| `--c-line-height-xs` | 1 | 紧凑布局 |
| `--c-line-height-sm` | 1.2 | 标题、短文本 |
| `--c-line-height-md` | 1.4 | 正文、段落 |
| `--c-line-height-lg` | 1.6 | 宽松文本 |
| `--c-line-height-xl` | 2 | 大段文字、阅读模式 |

#### 使用示例
```css
/* ✅ 正确：使用CSS变量 */
.card-title {
  font-size: var(--el-font-size-lg);
  font-weight: var(--el-font-weight-extra-bold);
  line-height: var(--c-line-height-sm);
}

.text-secondary {
  font-size: var(--el-font-size-xs);
  color: var(--el-text-color-secondary);
}

/* ❌ 错误：硬编码值 */
.card-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
}

.text-secondary {
  font-size: 12px;
  color: #909399;
}
```

#### 变量定义位置
所有字体变量定义在 `src/styles/themes.css` 中：
```css
/* ===== 字体大小 ===== */
--el-font-size-xxl: 22px;
--el-font-size-xl: 20px;
--el-font-size-lg: 18px;
--el-font-size-md: 16px;
--el-font-size-base: 14px;
--el-font-size-sm: 13px;
--el-font-size-xs: 12px;

/* ===== 字体权重变量 ===== */
--el-font-weight-extra-bold: 600;
--el-font-weight-bold: 500;
--el-font-weight-medium: 400;
--el-font-weight-regular: 300;

/* ===== 行高变量 ===== */
--c-line-height-xs: 1;
--c-line-height-sm: 1.2;
--c-line-height-md: 1.4;
--c-line-height-lg: 1.6;
--c-line-height-xl: 2;
```

### 3.5 BEM命名规范
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

### 3.6 Element Plus组件样式规范
- **使用 `:deep()` 选择器**：对于 Element Plus 组件，使用 `:deep()` 进行样式穿透
- **统一主题覆盖**：使用 CSS 变量覆盖 Element Plus 的默认主题
- **避免全局覆盖**：仅在必要时使用 `:deep()` 选择器，避免全局样式冲突

```css
/* Element Plus 表格样式 */
.data-card :deep(.el-table) {
  background-color: var(--white);
  border: none;
  border-radius: var(--app-border-radius);
}

.data-card :deep(.el-table thead th) {
  background-color: var(--light-gray);
  border-bottom: 1px solid var(--border_color);
  color: var(--font-color);
  font-size: var(--font-size-sm);
}
```

---

## 4. 代码组织规范

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

### 4.2 路径别名规范（强制）
**必须使用 `@/` 路径别名导入项目内部模块，禁止相对路径导入**

| 导入类型 | 正确写法 ✅ | 错误写法 ❌ |
|---------|------------|------------|
| API | `import { userApi } from '@/api'` | `import { userApi } from '../api'` |
| 组件 | `import BaseButton from '@/components/common/BaseButton.vue'` | `import BaseButton from '../../components/common/BaseButton.vue'` |
| 工具函数 | `import { formatDate } from '@/utils/format'` | `import { formatDate } from '../utils/format'` |
| Store | `import { useAuthStore } from '@/stores/auth'` | `import { useAuthStore } from '../stores/auth'` |

**优势：**
- ✅ 文件移动后无需修改导入路径
- ✅ 代码更清晰，统一使用绝对路径
- ✅ 避免 `../../../` 这种难以维护的相对路径

**配置说明：**
`vite.config.js` 中已配置 `@` 别名指向 `src` 目录：
```javascript
resolve: {
  alias: {
    '@': path.resolve(__dirname, 'src')
  }
}
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

## 5. JavaScript/TypeScript 规范

### 5.1 基本语法规范
- **使用 ES6+ 语法**：优先使用现代 JavaScript 语法
- **分号使用**：始终使用分号结束语句
- **引号使用**：使用单引号 `'` 或反引号 `` ` ``，避免使用双引号 `"`
- **缩进**：使用 2 个空格进行缩进
- **变量声明**：使用 `const` 或 `let`，避免使用 `var`

### 5.2 命名规范
| 类型 | 规范 | 示例 |
|-----|------|------|
| 变量/函数 | camelCase | `userName`, `fetchData` |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| 类/构造函数 | PascalCase | `UserService` |
| 布尔值 | is/has/can前缀 | `isActive`, `hasPermission` |

### 5.3 函数规范
- **函数长度**：尽量控制在 50 行以内
- **参数数量**：不超过 5 个，超过时使用对象参数
- **异步函数**：使用 `async/await` 处理异步操作

### 5.4 错误处理模板
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

## 6. Element 组件使用规范

Element Plus 组件使用规范已独立到单独文件，详见 [element-plus-components.md](./element-plus-components.md)。

**核心原则：**
- ✅ 使用 `:deep()` 选择器进行样式穿透
- ✅ 优先使用 CSS 变量覆盖主题
- ❌ 禁止直接修改 `.el-xxx` 类名
- ❌ 禁止使用 `!important`

---

## 7. 禁止事项

### 7.1 样式相关禁止
- ❌ **禁止**在页面文件中添加大量CSS样式
- ❌ **禁止**使用内联样式（除动态样式外）
- ❌ **禁止**使用硬编码颜色值、尺寸值
- ❌ **禁止**创建重复的样式定义
- ❌ **禁止**使用`!important`（极端情况除外）
- ❌ **禁止**直接修改`.el-xxx`类名的样式

### 7.2 代码结构禁止
- ❌ **禁止**违反导入顺序
- ❌ **禁止**在组件中混合业务逻辑和UI逻辑
- ❌ **禁止**创建重复的工具函数
- ❌ **禁止**使用非语义化HTML标签

### 7.3 命名规范禁止
- ❌ **禁止**混用命名规范（如`userName`和`user-name`混用）
- ❌ **禁止**使用过于通用的名称（如`data`、`item`、`component`）
- ❌ **禁止**使用缩写（除非是广泛认可的缩写）

---

## 8. 检查清单

在修改 `frontend/src/` 目录下的文件时，必须检查：

### 8.1 组件开发检查
- [ ] 是否使用了`<script setup>`语法？
- [ ] 是否明确定义了props和emits？
- [ ] 是否使用了语义化HTML标签？
- [ ] 是否遵循了导入顺序？
- [ ] 是否使用了CSS变量？
- [ ] 是否保持了组件样式最小化？

### 8.2 样式使用检查
- [ ] 是否优先使用了公共样式？
- [ ] 是否使用了CSS变量？
- [ ] 是否遵循了BEM命名规范？
- [ ] 是否避免了内联样式？
- [ ] 是否避免了硬编码值？

### 8.3 代码质量检查
- [ ] 是否遵循了命名规范？
- [ ] 是否保持了代码简洁？
- [ ] 是否添加了必要的注释？
- [ ] 是否处理了错误情况？

---

## 9. 核心原则

**简洁、一致、可维护**

1. **页面文件专注逻辑**，样式最小化
2. **优先使用公共资源**，避免重复造轮子
3. **严格遵循命名和组织规范**
4. **保持代码清晰和可维护性**
5. **强制使用CSS变量**，禁止硬编码值
