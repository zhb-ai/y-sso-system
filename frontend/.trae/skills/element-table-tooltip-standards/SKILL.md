---
name: "element-table-tooltip-standards"
description: "强制遵循Element Plus表格tooltip规范：el-table设置tooltip-effect='light'，描述/地址等可能溢出的列添加show-overflow-tooltip。在涉及Element Plus表格修改时必须调用此技能。"
---

# Element Plus 表格 Tooltip 规范

## 规范要求

### 1. 表格级别 tooltip-effect

所有 `el-table` 组件必须设置 `tooltip-effect="light"`：

```vue
<el-table
  :data="tableData"
  tooltip-effect="light"
  ...
>
```

### 2. 列级别 show-overflow-tooltip

以下类型的列**必须**添加 `show-overflow-tooltip` 属性：

- **描述类**: `description`, `desc`, `remark`, `note`, `comment`
- **地址类**: `address`, `url`, `link`, `path`
- **长文本类**: `content`, `detail`, `info`, `summary`
- **名称类**: 当 `min-width` 较大时（如 >150px）的 `name`, `title`

```vue
<!-- 描述列 -->
<el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />

<!-- 地址列 -->
<el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />

<!-- 长文本内容列 -->
<el-table-column prop="content" label="内容" min-width="250" show-overflow-tooltip />
```

### 3. 不需要添加的场景

以下情况**不需要**添加 `show-overflow-tooltip`：

- 有自定义 `template` 的列
- 固定宽度的短文本列（如 ID、状态等）
- 操作列

### 4. 完整示例

```vue
<template>
  <el-table
    :data="roles"
    tooltip-effect="light"
    style="width: 100%"
  >
    <el-table-column prop="id" label="ID" width="80" align="center" />
    <el-table-column prop="name" label="名称" min-width="120" />
    <el-table-column prop="code" label="编码" min-width="120" />
    <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
    <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
    <el-table-column label="操作" width="150" align="center">
      <template #default="scope">
        <el-button type="primary" link>编辑</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>
```

## 检查清单

修改表格时，请确认：

- [ ] `el-table` 是否设置了 `tooltip-effect="light"`
- [ ] 描述类列是否有 `show-overflow-tooltip`
- [ ] 地址类列是否有 `show-overflow-tooltip`
- [ ] 长文本类列是否有 `show-overflow-tooltip`
