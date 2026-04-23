---
name: "element-plus-dev-standards"
description: "强制遵循Element Plus开发规范：使用CSS变量而非硬编码值、不修改组件自带样式、不使用内联样式、使用标准CSS类和scoped样式。在涉及Element Plus样式修改时必须调用此技能。"
---

# Element Plus 开发规范

本文档汇总了所有 Element Plus 组件开发规范，包括表格、表单、对话框等组件的使用标准。

---

## 1. 表格组件 (el-table)

### 1.1 列宽度规范

**规则**: 列宽度必须 >= 标签字符数 × 40px

```vue
<!-- 正确 -->
<el-table-column label="主组织" width="120" />  <!-- 3×40=120 -->
<el-table-column label="员工编码" width="160" /> <!-- 4×40=160 -->

<!-- 错误 -->
<el-table-column label="主组织" width="90" />   <!-- 3×40=120, 90<120 -->
```

**例外情况**:
- 使用 `min-width` 的弹性列
- ID 列可用较小宽度 (70-80px)
- 操作列根据按钮数量调整

### 1.2 Tooltip 规范

**表格级别**: 必须设置 `tooltip-effect="light"`

```vue
<el-table :data="tableData" tooltip-effect="light">
```

**列级别**: 以下类型必须添加 `show-overflow-tooltip`

- 描述类: `description`, `desc`, `remark`, `note`
- 地址类: `address`, `url`, `link`, `path`
- 长文本类: `content`, `detail`, `info`
- 名称类: 当 `min-width > 150px` 时

```vue
<el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
<el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
```

**不需要添加的场景**:
- 有自定义 `template` 的列
- 固定宽度的短文本列（ID、状态等）
- 操作列

### 1.3 空状态处理

使用 `v-if` 控制，避免重复空提示：

```vue
<!-- 正确 -->
<el-table v-if="list.length > 0" :data="list">
  ...
</el-table>
<EmptyState v-else title="暂无数据" />

<!-- 错误 - 会显示两个空提示 -->
<el-table :data="list">
  ...
</el-table>
<EmptyState v-if="list.length === 0" />
```

### 1.4 样式覆盖

使用 `:deep()` 进行样式穿透：

```css
.data-card :deep(.el-table) {
  background-color: var(--white);
  border: none;
}

.data-card :deep(.el-table thead th) {
  background-color: var(--light-gray);
  border-bottom: 1px solid var(--border_color);
}
```

---

## 2. 表单组件 (el-form)

### 2.1 表单验证模式

**推荐方案** - 校验错误与 API 错误分离：

```typescript
const handleSubmit = async () => {
  if (!formRef.value) return
  
  // Step 1: 表单校验 - 失败直接返回
  const isValid = await formRef.value.validate().catch(() => false)
  if (!isValid) return  // Element Plus 自动显示错误
  
  // Step 2: 校验通过后才设置 loading
  submitLoading.value = true
  
  try {
    // API 调用 - 只有 API 错误会被 catch
    const response = await api.create(data)
    ElMessage.success('操作成功')
  } catch (error) {
    // 只处理 API 错误
    handleApiError(error, '操作失败')
  } finally {
    submitLoading.value = false
  }
}
```

**禁止方案** - 混合错误处理：

```typescript
// 不要这样做
const handleSubmit = async () => {
  try {
    await formRef.value.validate()  // 校验错误会进入 catch
    // ... API 调用
  } catch (error) {
    // 校验错误和 API 错误混在一起
    if (error.name || error.code) return  // 难以区分
    handleApiError(error, '失败')
  }
}
```

### 2.2 字段提示

使用 `label` 插槽添加提示：

```vue
<el-form-item>
  <template #label>
    函数名
    <el-tooltip content="用于筛选并查看某个缓存函数的统计与条目详情。" placement="top">
      <el-icon class="hint-icon"><QuestionFilled /></el-icon>
    </el-tooltip>
  </template>
  <el-select v-model="selectedFunctionName" />
</el-form-item>
```

### 2.3 密码输入框

防止自动填充：

```vue
<el-input
  v-model="password"
  type="password"
  placeholder="请输入密码"
  show-password
  autocomplete="new-password"
  :input-attrs="{ 
    autocomplete: 'new-password', 
    'data-lpignore': 'true', 
    'data-form-type': 'other' 
  }"
/>
```

**属性说明**:
- `autocomplete="new-password"` - HTML5 标准，告诉浏览器这是新密码
- `data-lpignore="true"` - 阻止 LastPass 自动填充
- `data-form-type="other"` - 告诉浏览器这不是登录表单

---

## 3. 对话框组件 (el-dialog)

### 3.1 基本规范

```vue
<el-dialog 
  v-model="visible" 
  title="标题" 
  width="500px"
  align-center
  destroy-on-close
>
  <template #default>
    <!-- 内容 -->
  </template>
  <template #footer>
    <el-button @click="visible = false">取消</el-button>
    <el-button type="primary" @click="handleConfirm">确定</el-button>
  </template>
</el-dialog>
```

### 3.2 抽屉替代方案

对于复杂表单，优先使用抽屉：

```vue
<el-drawer
  v-model="drawerVisible"
  title="编辑"
  size="820px"
  destroy-on-close
>
  <!-- 内容 -->
</el-drawer>
```

---

## 4. 按钮组件 (el-button)

### 4.1 图标按钮

只有图标时使用 `circle` 类型：

```vue
<el-button circle @click="toggleCollapse">
  <el-icon>
    <component :is="isCollapse ? ArrowRight : ArrowLeft" />
  </el-icon>
</el-button>
```

### 4.2 样式规范

- 优先使用内置 `type` 属性（primary, success, warning, danger, info）
- 自定义样式添加 class，通过 CSS 变量覆盖
- 禁止直接修改 `.el-button` 类名

---

## 5. 通用样式规范

### 5.1 使用 CSS 变量

```css
/* 正确 */
.custom-class {
  color: var(--el-color-primary);
  font-size: var(--el-font-size-base);
}

/* 错误 */
.custom-class {
  color: #409eff;
  font-size: 14px;
}
```

### 5.2 Scoped 样式

所有组件样式必须添加 `scoped`：

```vue
<style scoped>
.custom-class {
  /* ... */
}
</style>
```

### 5.3 禁止内联样式

```vue
<!-- 正确 -->
<div class="custom-class">

<!-- 错误 -->
<div style="color: red; font-size: 14px;">
```

---

## 6. 何时调用此技能

**必须调用**:
- 修改 Element Plus 组件样式
- 创建新的表格、表单、对话框
- 处理表单验证逻辑
- 涉及表格列宽度调整
- 添加 tooltip 或空状态

**建议调用**:
- 代码审查时检查 Element Plus 使用规范
- 重构现有组件

---

## 7. 相关技能

- `element-plus-migration` - 版本升级迁移问题
- `y-sso-frontend-standards` - 项目整体前端规范
- `ui-ux-pro-max` - UI/UX 优化
