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

## 5. Message 组件

### 5.1 消息提示
使用 `ElMessage` 进行消息提示：

```javascript
import { ElMessage } from 'element-plus'

// 成功提示
ElMessage.success('操作成功')

// 错误提示
ElMessage.error('操作失败')

// 警告提示
ElMessage.warning('请注意')

// 信息提示
ElMessage.info('提示信息')
```

---

## 6. 通用规范

### 6.1 样式覆盖原则
1. **禁止**直接修改 `.el-xxx` 类名的样式
2. **禁止**使用 `!important` 破坏组件原有样式
3. **必须**使用 `:deep()` 选择器进行样式穿透
4. **优先**使用 CSS 变量覆盖主题

### 6.2 图标使用
- 使用 `@element-plus/icons-vue` 提供的图标
- 图标大小通过 CSS 类控制，不使用内联样式

```vue
<el-icon class="icon-small"><HomeFilled /></el-icon>

<style scoped>
.icon-small {
  font-size: 16px;
}
</style>
```

### 6.3 尺寸规范
- 默认使用 Element Plus 默认尺寸
- 需要调整时使用 `size` 属性（large, default, small）
- 自定义尺寸通过 CSS 变量实现

---

## 更新日志

| 日期 | 更新内容 |
|-----|---------|
| 2026-03-16 | 初始版本，包含 Button、Form、Table、Dialog、Message 组件规范 |

---

**注意**：本文档将持续更新，添加更多组件的使用规范。在开发过程中遇到 Element Plus 组件使用问题，应及时更新本文档。
