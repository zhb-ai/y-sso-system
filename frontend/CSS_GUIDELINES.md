# 前端样式规范

## 目录

1. [设计原则](#1-设计原则)
2. [CSS 变量规范](#2-css-变量规范)
3. [选择器规范](#3-选择器规范)
4. [文件结构规范](#4-文件结构规范)
5. [组件样式规范](#5-组件样式规范)
6. [响应式设计规范](#6-响应式设计规范)
7. [动画和过渡效果](#7-动画和过渡效果)
8. [性能优化](#8-性能优化)
9. [代码格式规范](#9-代码格式规范)
10. [注释规范](#10-注释规范)
11. [设计系统](#11-设计系统)

---

## 1. 设计原则

### 1.1 核心原则
- **Ra-admin Bootstrap 风格**：严格遵循 Ra-admin 的 Bootstrap 设计语言
- **简洁明了**：避免复杂的渐变、阴影和动画，保持界面简洁清晰
- **一致性**：确保所有组件和页面使用统一的样式变量和设计模式
- **响应式设计**：适配不同屏幕尺寸，确保良好的移动端体验
- **可访问性**：确保颜色对比度、字体大小等符合可访问性标准

### 1.2 设计语言
- **颜色系统**：使用预定义的 CSS 变量，基于 Ra-admin 的色彩体系
- **排版**：采用清晰的层次结构，使用指定的字体大小和行高
- **间距**：使用一致的间距单位，确保布局整洁有序
- **阴影**：使用柔和的阴影效果，增强视觉层次感
- **圆角**：使用统一的圆角半径，保持设计一致性

---

## 2. CSS 变量规范

### 2.1 变量命名规则
- **语义化命名**：使用具有明确含义的命名，如 `--primary`, `--font-color`, `--border-radius`
- **功能分类**：按颜色、字体、间距、阴影等功能分类组织变量
- **层级结构**：使用连字符连接多词组合，如 `--font-title-color`
- **避免缩写**：除非是广泛认可的缩写（如 `btn` 代表 button）

### 2.2 变量使用原则
- **优先使用 CSS 变量**：所有样式属性应优先使用预定义的 CSS 变量
- **避免硬编码**：禁止直接使用颜色值、字体大小等硬编码值
- **主题一致性**：确保所有组件使用统一的主题变量
- **响应式变量**：为不同屏幕尺寸定义专门的间距和字体大小变量

### 2.3 标准变量定义

#### 颜色变量
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
  --black: 0, 0, 0;
  --white: #ffffff;
  
  /* 背景色 */
  --bodybg-color: #f9f9f9;
  --light-gray: #f4f7f8;
  --table-stripe-color: 245, 247, 250;
}
```

#### 字体变量
```css
:root {
  /* 字体家族 */
  --font-family-primary: "Golos Text", sans-serif;
  --font-family-mono: "SF Mono", Monaco, Inconsolata, "Roboto Mono", Consolas, "Courier New", monospace;
  
  /* 字体大小 */
  --font-size: 14px;
  --font-size-sm: 12px;
  --font-size-lg: 16px;
  
  /* 标题字体大小 */
  --h1-font-size: 2.5rem;
  --h2-font-size: 2rem;
  --h3-font-size: 1.75rem;
  --h4-font-size: 1.25rem;
  --h5-font-size: 1.125rem;
  --h6-font-size: 1rem;
  
  /* 字体颜色 */
  --font-color: #15264b;
  --font-title-color: #1c3264;
  --font-secondary-color: #22242c;
  --font-light-color: #a0a0b0;
  
  /* 行高 */
  --line-height: 1.6;
  --line-height-sm: 1.4;
  --line-height-lg: 1.8;
}
```

#### 间距变量
```css
:root {
  /* 基础间距 */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;
  
  /* 组件间距 */
  --card-padding: 1.5rem;
  --section-margin: 1.5rem;
  --element-gap: 1rem;
}
```

---

## 3. 选择器规范

### 3.1 选择器优先级原则
- **组件作用域优先**：使用 Vue 的 `scoped` 属性确保样式隔离
- **类选择器优先**：优先使用类选择器，避免 ID 选择器
- **避免嵌套过深**：选择器嵌套不超过 3 层
- **使用 BEM 命名**：对于复杂组件，使用 BEM 命名规范

### 3.2 BEM 命名规范
- **Block（块）**：组件的最外层容器，如 `.card`, `.button`
- **Element（元素）**：组件内部的子元素，使用双下划线连接，如 `.card__header`, `.button__icon`
- **Modifier（修饰符）**：组件的变体状态，使用双连字符连接，如 `.card--primary`, `.button--large`

### 3.3 选择器命名规则
- **语义化命名**：使用描述性强的类名，如 `.btn-primary`, `.card-header`
- **小写连字符**：使用小写字母和连字符组合，如 `.form-group`
- **组件前缀**：对于通用组件，添加前缀避免冲突，如 `.stat-card`, `.login-box`
- **状态类名**：使用明确的状態描述，如 `.is-active`, `.is-disabled`, `.has-error`

---

## 4. 文件结构规范

### 4.1 样式文件组织结构
```
src/styles/
├── index.css              # 主入口文件
├── base/                  # 基础样式
│   ├── variables.css      # CSS 变量定义
│   ├── reset.css         # 样式重置
│   ├── typography.css    # 字体排版
│   └── base.css          # 基础元素样式
├── layout/               # 布局样式
│   ├── layout.css        # 主布局
│   ├── header.css        # 头部布局
│   ├── sidebar.css       # 侧边栏布局
│   └── footer.css        # 底部布局
├── components/           # 组件样式
│   ├── ui/              # UI 组件
│   │   ├── buttons.css  # 按钮样式
│   │   ├── cards.css    # 卡片样式
│   │   ├── forms.css    # 表单样式
│   │   ├── tables.css   # 表格样式
│   │   └── modals.css   # 弹窗样式
│   ├── element-plus/    # Element Plus 覆盖样式
│   │   └── overrides.css
│   └── custom/          # 自定义组件
│       └── index.css
├── pages/               # 页面特定样式
│   ├── dashboard.css
│   ├── login.css
│   └── ...
├── themes/              # 主题样式
│   ├── light.css
│   └── dark.css
└── utilities/           # 工具类
    ├── spacing.css     # 间距工具类
    ├── colors.css      # 颜色工具类
    ├── text.css        # 文本工具类
    └── index.css       # 工具类入口
```

### 4.2 文件命名规范
- **小写连字符**：使用小写字母和连字符组合
- **语义化命名**：文件名应清晰反映文件内容
- **模块化命名**：按功能模块命名，如 `buttons.css`, `forms.css`
- **避免冗余**：文件名应简洁明了，避免重复信息

---

## 5. 组件样式规范

### 5.1 组件基础样式规范
- **统一容器样式**：所有页面容器使用一致的内边距和背景色
- **卡片样式统一**：统一卡片的边框、阴影和圆角
- **按钮样式统一**：统一按钮的尺寸、颜色和过渡效果
- **表单样式统一**：统一输入框、选择器等表单元素的样式

### 5.2 Element Plus 组件样式规范
- **使用 `:deep()` 选择器**：对于 Element Plus 组件，使用 `:deep()` 进行样式穿透
- **统一主题覆盖**：使用 CSS 变量覆盖 Element Plus 的默认主题
- **避免全局覆盖**：仅在必要时使用 `:deep()` 选择器，避免全局样式冲突
- **组件特定样式**：将 Element Plus 组件样式限定在特定组件范围内

### 5.3 组件样式示例
```css
/* 卡片组件样式 */
.card {
  background-color: var(--white);
  border-radius: var(--app-border-radius);
  box-shadow: var(--box-shadow);
  transition: var(--app-transition);
  padding: var(--card-padding);
  margin-bottom: var(--section-margin);
  border: 1px solid var(--border_color);
}

.card:hover {
  box-shadow: var(--hover-shadow);
  transform: translateY(-2px);
}

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

## 6. 响应式设计规范

### 6.1 断点系统
使用预定义的 CSS 变量作为断点，与 Bootstrap 保持一致：
```css
:root {
  --breakpoint-xs: 0;
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
  --breakpoint-2xl: 1400px;
}
```

### 6.2 响应式设计原则
- **移动优先设计**：先设计移动端，再逐步适配更大屏幕
- **弹性布局**：优先使用 Flexbox 和 Grid 布局
- **媒体查询**：使用预定义的断点变量
- **适配策略**：针对不同屏幕尺寸调整布局、字体大小和间距

### 6.3 响应式样式示例
```css
/* 默认移动端样式 */
.stats-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-md);
}

/* 平板端样式 */
@media (min-width: 768px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 桌面端样式 */
@media (min-width: 992px) {
  .stats-cards {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-lg);
  }
}
```

---

## 7. 动画和过渡效果

### 7.1 过渡效果规范
- **统一过渡时间**：使用 `--app-transition` 变量定义统一的过渡时间
- **平滑过渡**：为 hover、focus 等状态添加平滑过渡
- **性能优化**：使用 transform 和 opacity 属性实现过渡效果
- **避免过度动画**：仅在必要时使用动画，避免影响性能

### 7.2 动画规范
- **简洁明了**：避免复杂的动画效果
- **性能优先**：使用 CSS 动画而非 JavaScript 动画
- **用途明确**：动画应增强用户体验，而非单纯装饰
- **可访问性考虑**：为动画添加 `prefers-reduced-motion` 媒体查询支持

### 7.3 过渡效果示例
```css
/* 基础过渡效果 */
.card {
  transition: var(--app-transition);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--hover-shadow);
}

/* 按钮过渡效果 */
.btn {
  transition: all 0.2s ease-in-out;
}

.btn:hover {
  transform: scale(1.02);
}

/* 可访问性优化 */
@media (prefers-reduced-motion: reduce) {
  .card,
  .btn {
    transition: none;
  }
}
```

---

## 8. 性能优化

### 8.1 样式性能优化
- **减少重排重绘**：避免频繁修改布局属性
- **使用 CSS 变量**：便于主题切换和样式统一
- **避免 `!important`**：仅在极端情况下使用
- **简化选择器**：减少选择器复杂度和嵌套深度
- **使用高效属性**：优先使用 transform 和 opacity 进行动画

### 8.2 资源优化
- **压缩 CSS**：确保生产环境使用压缩后的 CSS
- **减少样式文件大小**：移除未使用的样式
- **使用 CSS 变量替代重复值**：减少代码冗余
- **按需加载样式**：根据组件需要加载对应的样式文件

### 8.3 渲染性能优化
- **避免深层嵌套**：保持选择器简洁
- **使用类选择器**：避免使用标签选择器和通配符选择器
- **减少样式计算**：避免复杂的 CSS 表达式
- **优化重排属性**：避免频繁修改 width、height、margin 等属性

---

## 9. 代码格式规范

### 9.1 缩进和空格规范
- **使用 2 个空格进行缩进**（不使用 tab）
- **在选择器和 `{` 之间添加空格**
- **在属性名和 `:` 之间不添加空格**
- **在 `:` 和属性值之间添加空格**
- **在 `;` 之后添加换行**
- **在相邻的规则集之间添加空行**

### 9.2 代码组织规范
- **按功能模块组织样式**
- **为相关样式添加注释**
- **使用空行分隔不同功能的样式块**
- **按字母顺序排列属性**（推荐，保持一致性）
- **分组相关属性**：布局属性、盒模型属性、字体属性、视觉属性

### 9.3 代码格式示例
```css
/* 卡片样式 */
.card {
  /* 布局属性 */
  display: flex;
  flex-direction: column;
  
  /* 盒模型属性 */
  padding: var(--card-padding);
  margin-bottom: var(--section-margin);
  border: 1px solid var(--border_color);
  border-radius: var(--app-border-radius);
  
  /* 视觉属性 */
  background-color: var(--white);
  box-shadow: var(--box-shadow);
  transition: var(--app-transition);
}

.card:hover {
  box-shadow: var(--hover-shadow);
  transform: translateY(-2px);
}
```

---

## 10. 注释规范

### 10.1 注释格式规范
- **单行注释**：使用 `/* 注释内容 */` 格式
- **多行注释**：对于复杂样式块，使用多行注释
- **描述性注释**：注释应说明样式的用途和功能
- **避免冗余注释**：不要注释显而易见的代码

### 10.2 注释使用场景
- **文件开头**：说明文件用途和结构
- **重要样式块**：说明样式的功能和使用场景
- **特殊样式**：说明特殊处理的原因
- **响应式样式**：说明适配的屏幕尺寸
- **临时样式**：标记临时或实验性的样式

### 10.3 注释示例
```css
/**
 * 卡片组件样式
 * 
 * 本文件定义了卡片组件的基础样式，包括默认状态、悬停状态和响应式适配。
 * 遵循 Ra-admin Bootstrap 设计语言和项目CSS规范。
 */

/* ==================================================================
   01. 基础卡片样式
   ================================================================== */

.card {
  /* 使用主题色作为边框颜色 */
  border-color: var(--border_color);
  /* 卡片阴影效果 - 增强视觉层次 */
  box-shadow: var(--box-shadow);
  /* 卡片过渡动画 - 提升交互体验 */
  transition: var(--app-transition);
}

/* ==================================================================
   02. 卡片悬停效果
   ================================================================== */

/* 桌面端悬停效果 - 仅在非触摸设备上启用 */
@media (hover: hover) {
  .card:hover {
    transform: translateY(-2px);
    box-shadow: var(--hover-shadow);
  }
}
```

---

## 11. 设计系统

### 11.1 颜色系统设计
- **主色调**：`--primary` (72, 190, 206) - 用于主要按钮、链接、高亮等
- **辅助色调**：`--secondary`, `--success`, `--danger`, `--warning`, `--info` - 用于不同状态的提示和操作
- **中性色调**：`--light`, `--dark`, `--white`, `--black` - 用于文本、背景等
- **背景色调**：`--bodybg-color`, `--light-gray` - 用于页面和组件背景
- **语义化颜色**：每个颜色都有明确的用途和含义

### 11.2 字体系统设计
- **字体层级**：基于 `--font-size` (14px) 构建清晰的字体大小层级
- **行高系统**：统一的行高比例，确保文本可读性
- **字重系统**：使用 400, 500, 600, 700 四个字重，每个都有明确用途
- **字体家族**：主字体和等宽字体分开定义，满足不同场景需求

### 11.3 间距系统设计
- **基础间距单位**：基于 0.25rem 的倍数构建间距系统
- **组件间距**：为不同组件定义专门的间距变量
- **响应式间距**：在不同屏幕尺寸下使用不同的间距值
- **一致性原则**：相同功能的元素使用相同的间距值

### 11.4 组件设计模式
- **卡片模式**：统一的卡片样式，包含圆角、阴影、边框等
- **按钮模式**：不同尺寸和状态的按钮样式
- **表单模式**：输入框、选择器等表单元素的统一样式
- **表格模式**：数据表格的头部、行、单元格样式规范

---

## 总结

本样式规范基于 Ra-admin Bootstrap 设计语言，旨在确保项目的一致性、可维护性和性能。所有开发人员必须严格遵循本规范，确保：

1. **代码一致性**：所有样式代码风格统一，易于维护
2. **性能优化**：样式代码高效，不影响页面渲染性能
3. **可扩展性**：规范具有良好的扩展性，支持项目发展
4. **团队协作**：规范明确，便于团队成员理解和遵循

随着项目的发展，本规范将定期更新和完善。如有疑问或建议，请及时与团队沟通。