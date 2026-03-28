---
name: "vue-flow-workflow"
description: "Implements Vue Flow workflow diagrams with custom nodes, edges, and styling. Invoke when user needs to create or modify approval flows, process diagrams, or node-based visualizations using Vue Flow."
---

# Vue Flow 流程图实现规范

## 核心实现方式

### 1. 使用模板插槽自定义节点

必须使用 `<template #node-custom="nodeProps">` 方式定义自定义节点，而不是使用 markRaw + render 函数。

```vue
<VueFlow v-model:nodes="nodes" v-model:edges="edges">
  <!-- 自定义节点模板 -->
  <template #node-custom="nodeProps">
    <div 
      class="custom-node"
      :class="['type-' + nodeProps.data.type, { 'node-selected': nodeProps.selected }]"
    >
      <div class="node-content">
        <div class="node-header">
          <div class="node-icon-wrapper" :class="'bg-' + nodeProps.data.type">
            <div class="node-icon">
              <el-icon>
                <component :is="getNodeIcon(nodeProps.data.type)" />
              </el-icon>
            </div>
          </div>
          <div class="node-type-badge" :class="'badge-' + nodeProps.data.type">
            {{ getNodeTypeName(nodeProps.data.type) }}
          </div>
        </div>
        <div class="node-body">
          <div class="node-name">{{ nodeProps.label }}</div>
          <!-- 其他节点内容 -->
        </div>
      </div>
      <!-- 节点配置按钮 -->
      <el-button 
        class="node-config-btn"
        type="primary"
        link
        size="small"
        @click="openNodeConfig(nodeProps.data)"
      >
        <el-icon><Setting /></el-icon>
      </el-button>
      <!-- 连接点 - 横向流程：右侧出，左侧入 -->
      <Handle type="target" :position="Position.Left" />
      <Handle type="source" :position="Position.Right" />
    </div>
  </template>
</VueFlow>

<!-- 节点配置 Drawer -->
<el-drawer
  v-model="drawerVisible"
  title="节点配置"
  size="400px"
  :with-header="true"
>
  <div v-if="selectedNode" class="node-properties">
    <!-- 节点配置表单 -->
  </div>
</el-drawer>
```

### 2. 导入必要的组件

**重要**：Controls、Background 和 MiniMap 需要单独安装对应的包。

```bash
# 安装必要的包
npm install @vue-flow/controls
npm install @vue-flow/background
npm install @vue-flow/minimap
```

```typescript
import { VueFlow, useVueFlow, Handle, Position, ConnectionMode, MarkerType } from '@vue-flow/core'
import { Controls } from '@vue-flow/controls'
import { Background, BackgroundVariant } from '@vue-flow/background'
import { MiniMap } from '@vue-flow/minimap'

// 导入样式文件
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
```

**注意**：`@vue-flow/background` 包不包含独立的样式文件，其样式已内联在组件中。

### 3. 边配置使用 ConnectionMode.Strict

```vue
<VueFlow
  v-model:nodes="nodes"
  v-model:edges="edges"
  :connection-mode="ConnectionMode.Strict"
  :default-edge-options="{
    animated: true,  // 默认开启动画
    style: {
      stroke: '#909399',
      strokeWidth: 2,
      strokeDasharray: '5,5'  // 虚线
    },
    markerEnd: {
      type: 'arrow',
      width: 10,
      height: 10,
      color: '#909399'
    }
  }"
  fit-view-on-init
>
```

**注意**：`type` 属性使用默认值，不需要在 `default-edge-options` 中配置。

### 4. 节点样式规范

#### 边框颜色（根据类型）
```css
.custom-node.type-start { border-color: #67C23A; }
.custom-node.type-approval { border-color: #409EFF; }
.custom-node.type-condition { border-color: #E6A23C; }
.custom-node.type-leave { border-color: #F56C6C; }
.custom-node.type-expense { border-color: #909399; }
.custom-node.type-end { border-color: #C0C4CC; }
```

#### Icon 背景色
```css
.node-icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-icon-wrapper.bg-start { background-color: rgba(103, 194, 58, 0.15); }
.node-icon-wrapper.bg-approval { background-color: rgba(64, 158, 255, 0.15); }
/* ... 其他类型 */
```

#### Icon 颜色
```css
.node-icon-wrapper.bg-start .node-icon { color: #67C23A; }
.node-icon-wrapper.bg-approval .node-icon { color: #409EFF; }
/* ... 其他类型 */
```

### 5. 节点位置布局

默认节点应该合理设置 position，使流程图横向排布美观：

```typescript
const nodes = ref<FlowNode[]>([
  {
    id: '1',
    type: 'custom',
    label: '开始',
    position: { x: 50, y: 150 },
    data: { type: 'start', ... }
  },
  {
    id: '2',
    type: 'custom',
    label: '审批',
    position: { x: 300, y: 150 },  // x 轴间隔 250px
    data: { type: 'approval', ... }
  },
  {
    id: '3',
    type: 'custom',
    label: '条件判断',
    position: { x: 550, y: 150 },
    data: { type: 'condition', ... }
  },
  // ... 后续节点
])
```

### 6. 节点库设计与拖放功能

- 默认隐藏，点击左上角按钮显示
- 按钮使用 Plus/Close 图标切换
- 节点库从按钮下方滑出
- 支持拖拽节点到画布上添加

```vue
<!-- 节点库切换按钮 - 左上角 -->
<div class="library-toggle" @click="toggleNodeLibrary">
  <el-button type="primary" circle size="small">
    <el-icon><Plus v-if="!nodeLibraryVisible" /><Close v-else /></el-icon>
  </el-button>
</div>

<!-- 左上角悬浮节点库 -->
<div class="node-library" :class="{ show: nodeLibraryVisible }">
  <div class="node-types">
    <div
      v-for="type in nodeTypes"
      :key="type.value"
      class="node-type-item"
      draggable="true"
      @dragstart="onDragStart($event, type.value)"
    >
      <el-icon><component :is="type.icon" /></el-icon>
      <span>{{ type.label }}</span>
    </div>
  </div>
</div>
```

### 7. 拖放功能实现

```typescript
// 拖放状态
const isDragOver = ref(false)
const draggedNodeType = ref<string | null>(null)

// Vue Flow 实例
const { fitView, addNodes, project } = useVueFlow()

// 开始拖拽
const onDragStart = (event: DragEvent, type: string) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', type)
    event.dataTransfer.effectAllowed = 'move'
    draggedNodeType.value = type
  }
}

// 拖拽经过画布
const onDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  isDragOver.value = true
}

// 拖拽离开画布
const onDragLeave = () => {
  isDragOver.value = false
}

// Vue Flow 实例 - 需要 onConnect 和 addEdges 实现节点连接
const { fitView, addNodes, project, onConnect, addEdges } = useVueFlow()

// 节点连接事件 - 实现从节点拖拽到另一个节点连接
onConnect((connection) => {
  const newEdge = {
    id: `e${connection.source}-${connection.target}`,
    source: connection.source,
    target: connection.target,
    data: {}
  }
  addEdges([newEdge])
})

// 放置节点
const onDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false

  const type = event.dataTransfer?.getData('application/vueflow')
  if (!type) return

  // 获取 Vue Flow 容器的位置
  const flowElement = document.querySelector('.vue-flow') as HTMLElement
  if (!flowElement) return

  const flowRect = flowElement.getBoundingClientRect()

  // 计算相对于画布的位置 - 使用 clientX/clientY 减去容器偏移
  const position = project({
    x: event.clientX - flowRect.left,
    y: event.clientY - flowRect.top
  })

  // 创建新节点
  const newNode = {
    id: Date.now().toString(),
    type: 'custom',
    label: getNodeLabel(type),
    position,
    data: { type, ... }
  }

  addNodes([newNode])
  draggedNodeType.value = null
}
```

```vue
<VueFlow
  v-model:nodes="nodes"
  v-model:edges="edges"
  @dragover="onDragOver"
  @dragleave="onDragLeave"
  @drop="onDrop"
  class="custom-node-flow"
  :class="{ 'drag-over': isDragOver }"
>
  <!-- ... -->
</VueFlow>
```

```css
/* 拖放时的画布样式 */
.custom-node-flow.drag-over {
  background-color: rgba(64, 158, 255, 0.05);
}

.custom-node-flow {
  transition: background-color 0.2s ease;
}

/* 可拖拽节点项样式 */
.node-type-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  cursor: grab;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.node-type-item:hover {
  background-color: #ecf5ff;
  border-color: #409EFF;
  color: #409EFF;
}

.node-type-item:active {
  cursor: grabbing;
}
```

### 7. 辅助函数

```typescript
const getNodeIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'start': 'CircleCheck',
    'approval': 'User',
    'condition': 'Filter',
    'leave': 'Calendar',
    'expense': 'Money',
    'end': 'CircleClose'
  }
  return iconMap[type] || 'Circle'
}

const getNodeTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    'start': '开始',
    'approval': '审批',
    'condition': '条件',
    'leave': '请假',
    'expense': '报销',
    'end': '结束'
  }
  return typeMap[type] || '节点'
}

const getHandleColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'start': '#67C23A',
    'approval': '#409EFF',
    'condition': '#E6A23C',
    'leave': '#909399',
    'expense': '#F56C6C',
    'end': '#909399'
  }
  return colorMap[type] || '#909399'
}
```

## 完整示例结构

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background, Controls, MiniMap } from '@vue-flow/additional-components'
import '@vue-flow/core/dist/style.css'

// 节点和边数据
const nodes = ref([...])
const edges = ref([...])

// 辅助函数
const getNodeIcon = (type: string) => { ... }
const getNodeTypeName = (type: string) => { ... }
const getHandleColor = (type: string) => { ... }
</script>

<template>
  <VueFlow
    v-model:nodes="nodes"
    v-model:edges="edges"
    :connection-mode="ConnectionMode.Strict"
    :default-edge-options="{...}"
    fit-view-on-init
  >
    <template #node-custom="nodeProps">
      <!-- 自定义节点内容 -->
    </template>
    
    <Background pattern-color="#f0f0f0" :gap="20" />
    <Controls position="bottom-right" />
    <MiniMap />
  </VueFlow>
</template>

<style scoped>
/* 节点样式 */
.custom-node { ... }

/* 类型边框 */
.custom-node.type-start { border-color: #67C23A; }
/* ... */

/* Icon 背景 */
.node-icon-wrapper.bg-start { background-color: rgba(103, 194, 58, 0.15); }
/* ... */
</style>
```

## 布局规范

### 容器布局

流程图容器不应该有左右边距，宽度应与页面标题卡片对齐，避免出现横向滚动条：

```css
.approval-container {
  display: flex;
  height: calc(100vh - 220px);
  position: relative;
  /* 不要添加 padding 左右边距 */
}

.flow-container {
  flex: 1;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
}
```

### 节点配置按钮样式

```css
.node-config-btn {
  margin-left: auto;
  padding: 4px !important;
  height: auto !important;
}

.node-config-btn .el-icon {
  font-size: 14px;
}
```

## 注意事项

1. 必须使用模板插槽方式定义节点，不要使用 markRaw + render
2. 边使用 ConnectionMode.Strict 确保连接规范
3. 节点位置要合理设置，x 轴间隔 250px 左右，y 轴保持一致
4. 使用 Handle 组件定义连接点，横向流程只保留左右两个连接点
5. 边样式使用虚线和曲线过渡（smoothstep）
6. **默认设计不应该出现横向滚动条**，确保容器宽度与父元素对齐
7. 节点配置使用 Element Drawer 组件从右侧弹出，而不是固定宽度的侧边栏
