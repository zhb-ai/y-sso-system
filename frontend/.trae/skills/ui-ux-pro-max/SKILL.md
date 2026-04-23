---
name: "ui-ux-pro-max"
description: "一站式 UI/UX 优化专家，自动执行完整的设计优化流程。Invoke when user wants comprehensive UI/UX improvements, full page optimization, or 'make this look professional'."
---

# UI/UX Pro Max

一站式 UI/UX 优化专家，自动执行完整的设计优化流程，从诊断到最终交付。

## 触发条件

当用户说以下话时调用：
- "优化这个页面"
- "让界面更专业"
- "改进 UI/UX"
- "美化这个页面"
- "提升界面品质"
- "完整优化"
- "professional UI"
- "make it look good"
- "improve the design"

## 执行流程

```
第一阶段：诊断和准备（自动执行）
├── 1. 检查 teach-impeccable 是否已运行
│   └── 如果未运行，提示用户先运行 teach-impeccable
├── 2. web-design-guidelines
│   └── 根据 Vercel Web Interface Guidelines 审查代码
└── 3. audit
    └── 全面审查界面质量

第二阶段：结构性优化
├── 4. normalize
│   └── 规范化到设计系统
├── 5. distill
│   └── 简化不必要的复杂性
└── 6. arrange
    └── 优化布局和间距

第三阶段：视觉优化
├── 7. typeset
│   └── 优化字体排版
├── 8. colorize（谨慎使用）
│   └── 仅在界面过于单调时添加战略性颜色
└── 9. bolder/quieter（按需）
    └── 根据当前设计强度调整

第四阶段：交互优化
├── 10. animate
│   └── 添加动画和微交互
├── 11. clarify
│   └── 优化文案
└── 12. delight（可选）
    └── 添加惊喜时刻

第五阶段：健壮性和适配
├── 13. harden
│   └── 错误处理和边缘情况
├── 14. adapt
│   └── 响应式适配
└── 15. onboard
    └── 优化空状态和引导

第六阶段：最终交付
├── 16. extract
│   └── 提取可复用组件
├── 17. optimize
│   └── 性能优化
└── 18. polish
    └── 最终润色
```

## 使用方式

### 基础用法
```
ui-ux-pro-max
```
自动优化当前文件或整个项目。

### 指定文件
```
ui-ux-pro-max src/pages/users/Index.vue
```

### 指定目录
```
ui-ux-pro-max src/pages/
```

### 快速模式（跳过可选步骤）
```
ui-ux-pro-max --quick
```
跳过 bolder/quieter、delight 等可选步骤。

### 仅视觉优化
```
ui-ux-pro-max --visual-only
```
只执行视觉相关优化（normalize、arrange、typeset、colorize、animate、polish）。

## 输出

执行完成后会生成：
1. **优化报告** - 列出所有修改和改进点
2. **前后对比** - 关键改动的前后对比
3. **设计系统更新** - 如果有新的可复用组件

## 注意事项

1. **必须先运行 teach-impeccable** - 确保设计上下文已建立
2. **备份重要代码** - 虽然会谨慎修改，但建议先提交代码
3. **分阶段执行** - 大型项目建议分页面执行，避免一次改动过多
4. **审查改动** - 执行后请审查所有修改，确保符合预期

## 与其他 Skill 的关系

- **teach-impeccable**: 前置依赖，必须先运行
- **normalize/arrange/typeset**: 被 ui-ux-pro-max 自动调用
- **polish**: 最终步骤，确保交付质量
- **extract**: 识别可复用组件，丰富设计系统
