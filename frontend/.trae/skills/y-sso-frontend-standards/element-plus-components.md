# Element Plus 组件使用规范

本文档定义了项目中 Element Plus 组件的使用规范，将持续更新维护。

---

## 1. Button 组件

### 1.1 图标按钮
当按钮中只有图标没有文案时，推荐使用 `circle` 类型：

```vue
<el-button circle class="collapse-btn" @click="toggleCollapse">
  <el-icon>
    <component :is="isCollapse ? ArrowRight : ArrowLeft" />
  </el-icon>
</el-button>
```

### 1.2 按钮样式规范
- 优先使用 Element Plus 内置的 `type` 属性（primary, success, warning, danger, info）
- 需要自定义样式时，添加自定义 class，通过 CSS 变量覆盖
- 禁止直接修改 `.el-button` 类名

---

## 2. Form 组件

### 2.1 表单字段提示
当需要为表单字段添加提示信息时，推荐使用 `el-form-item` 的 `label` 插槽：

```vue
<el-form-item>
  <template #label>
    函数名
    <el-tooltip content="用于筛选并查看某个缓存函数的统计与条目详情。" placement="top">
      <el-icon class="hint-icon form-item-hint"><QuestionFilled /></el-icon>
    </el-tooltip>
  </template>
  <el-select v-model="selectedFunctionName" filterable clearable placeholder="请选择缓存函数">
    <el-option
      v-for="item in functions"
      :key="item[CACHE_FUNCTION_COLUMNS.NAME]"
      :label="item[CACHE_FUNCTION_COLUMNS.NAME]"
      :value="item[CACHE_FUNCTION_COLUMNS.NAME]"
    />
  </el-select>
</el-form-item>
```

### 2.2 表单验证
- 使用 `rules` 属性定义验证规则
- 验证规则统一放在 `utils/validation.js` 中
- 错误提示使用中文

---

## 3. Table 组件

### 3.1 表格样式覆盖
使用 `:deep()` 选择器进行样式穿透：

```css
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

### 3.2 表格操作
- 操作按钮使用 `el-button` 的 `link` 类型
- 多个操作按钮之间添加分隔符

---

## 4. Dialog 组件

### 4.1 弹窗规范
- 使用 `v-model` 控制显示/隐藏
- 标题使用 `title` 属性或 `header` 插槽
- 底部按钮使用 `footer` 插槽

```vue
<el-dialog v-model="visible" title="标题" width="500px">
  <template #default>
    <!-- 内容 -->
  </template>
  <template #footer>
    <el-button @click="visible = false">取消</el-button>
    <el-button type="primary" @click="handleConfirm">确定</el-button>
  </template>
</el-dialog>
```

---

## 5. Switch 组件

### 5.1 带文案的 Switch 规范

当 Switch 组件需要显示切换文案（如"启用/禁用"）时，**必须**使用以下标准配置：

```vue
<el-switch
  v-model="scope.row.is_active"
  @change="handleStatusChange(scope.row)"
  :active-action-icon="Check"
  :inactive-action-icon="Close"
  active-text="启用"
  inactive-text="禁用"
  inline-prompt
/>
```

**必需属性说明：**

| 属性 | 值 | 说明 |
|-----|---|------|
| `active-action-icon` | `Check` (从 @element-plus/icons-vue 导入) | 开启状态的图标 |
| `inactive-action-icon` | `Close` (从 @element-plus/icons-vue 导入) | 关闭状态的图标 |
| `active-text` | 根据业务定义，如"启用" | 开启状态的文字 |
| `inactive-text` | 根据业务定义，如"禁用" | 关闭状态的文字 |
| `inline-prompt` | - | 将文字显示在 Switch 内部 |

**使用场景：**
- 表格中的状态切换列
- 需要明确标识开关含义的场景
- 启用/禁用、是/否等二元状态

**注意事项：**
- 必须同时配置 `active-text` 和 `inactive-text`
- 必须添加 `inline-prompt` 属性
- 图标统一使用 `Check` 和 `Close`
- 事件处理使用 `@change` 而非 `@input`

### 5.2 纯图标 Switch（无文案）

当不需要显示文案时，仅使用图标：

```vue
<el-switch
  v-model="value"
  :active-action-icon="Check"
  :inactive-action-icon="Close"
/>
```

### 5.3 简单 Switch（无图标无文案）

最简配置，仅保留基础功能：

```vue
<el-switch v-model="value" />
```

---

## 6. 其他组件

### 6.1 图标使用
- 统一从 `@element-plus/icons-vue` 导入
- 使用 `<component :is="IconName" />` 方式动态切换

### 6.2 输入框
- 非登录页输入框必须添加 `autocomplete="off"`
- 手机号输入框使用 `autocomplete="new-phone"` 阻止自动填充
- 密码输入框使用 `autocomplete="new-password"`
