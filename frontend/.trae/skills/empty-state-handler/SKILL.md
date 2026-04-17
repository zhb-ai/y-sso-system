---
name: "empty-state-handler"
description: "处理组件重复空提示问题。当页面同时使用自定义 EmptyState 组件和 Element Plus 组件（如 el-table、el-tree）的默认空提示时，会出现两个空提示重叠。Invoke when user reports duplicate empty state messages or when reviewing list/table pages with custom empty states."
---

# Empty State Handler

处理 Vue 页面中重复空提示的问题。

## 问题描述

当页面同时满足以下条件时，会出现两个空提示：
1. 使用 Element Plus 组件（el-table、el-tree 等）显示列表数据
2. 组件有默认的 "暂无数据" 空提示
3. 页面又使用了自定义的 EmptyState 组件作为空状态展示

## 解决方案

使用 `v-if` 条件判断，当数据为空时隐藏 Element Plus 组件，只显示自定义 EmptyState。

### 修复前（问题代码）

```vue
<template>
  <div>
    <!-- 问题：el-table 会显示默认的 "暂无数据" -->
    <el-table :data="list">
      <el-table-column prop="name" label="名称" />
    </el-table>
    
    <!-- 问题：同时显示自定义空提示 -->
    <EmptyState
      v-if="list.length === 0"
      title="暂无数据"
      description="还没有创建任何数据"
    />
  </div>
</template>
```

### 修复后（正确代码）

```vue
<template>
  <div>
    <!-- 修复：数据为空时不渲染 el-table -->
    <el-table v-if="list.length > 0" :data="list">
      <el-table-column prop="name" label="名称" />
    </el-table>
    
    <!-- 修复：只显示自定义空提示 -->
    <EmptyState
      v-else
      title="暂无数据"
      description="还没有创建任何数据"
    />
  </div>
</template>
```

## 常见场景

### 1. el-table + EmptyState

```vue
<!-- 修复前 -->
<el-table :data="applications" v-loading="loading">
  <!-- columns -->
</el-table>
<EmptyState v-if="!loading && applications.length === 0" ... />

<!-- 修复后 -->
<el-table v-if="applications.length > 0" :data="applications" v-loading="loading">
  <!-- columns -->
</el-table>
<EmptyState v-else-if="!loading" ... />
```

### 2. el-tree + EmptyState

```vue
<!-- 修复前 -->
<el-tree :data="treeData" />
<EmptyState v-if="treeData.length === 0" ... />

<!-- 修复后 -->
<el-tree v-if="treeData.length > 0" :data="treeData" />
<EmptyState v-else ... />
```

### 3. 考虑 loading 状态

```vue
<template>
  <div>
    <!-- 有数据时显示表格 -->
    <el-table v-if="list.length > 0" :data="list" v-loading="loading">
      <!-- columns -->
    </el-table>
    
    <!-- 加载中显示 loading（可选）-->
    <div v-else-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    
    <!-- 无数据时显示自定义空提示 -->
    <EmptyState v-else ... />
  </div>
</template>
```

## 检查清单

修复页面时，检查以下 Element Plus 组件：

- [ ] `el-table` - 默认显示 "暂无数据"
- [ ] `el-tree` - 默认显示 "暂无数据"
- [ ] `el-transfer` - 默认显示空提示
- [ ] `el-cascader-panel` - 默认显示空提示
- [ ] `el-select` (多选/远程搜索) - 可能显示空提示
- [ ] `el-autocomplete` - 可能显示空提示
- [ ] `el-upload` - 空列表时显示提示

## 代码审查要点

1. **搜索模式**：查找 `EmptyState` 组件和 `el-table`/`el-tree` 同时使用的文件
2. **条件判断**：确保使用 `v-if`/`v-else` 互斥显示
3. **loading 处理**：考虑加载状态，避免闪烁
4. **一致性**：确保所有列表页面使用相同的处理模式

## 示例修复

```vue
<!-- 修复前：applications/Index.vue -->
<el-table :data="applications" v-loading="loading">
  <!-- ... -->
</el-table>

<EmptyState
  v-if="!loading && applications.length === 0"
  type="data"
  title="暂无应用"
  description="还没有创建任何应用"
/>

<!-- 修复后：applications/Index.vue -->
<el-table v-if="applications.length > 0" :data="applications" v-loading="loading">
  <!-- ... -->
</el-table>

<EmptyState
  v-else-if="!loading"
  type="data"
  title="暂无应用"
  description="还没有创建任何应用"
/>
```
