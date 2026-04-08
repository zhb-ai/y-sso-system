# Vue 3 + Vite

初始化项目 使用 skills/vue3-project-initializer 初始化项目结构

---

## Skills 使用指南

本项目使用 `.agents/skills/` 目录下的 Skills 来优化页面。以下是所有 Skill 的说明、触发条件和推荐调用顺序。

### Skill 列表

| Skill | 功能描述 | 触发关键词 |
|-------|----------|-----------|
| **web-design-guidelines** | 根据 Web Interface Guidelines 审查 UI 代码合规性 | "review my UI", "check accessibility", "audit design", "review UX", "check my site against best practices" |
| **audit** | 全面审查界面质量（可访问性、性能、主题、响应式） | "review my UI", "check accessibility", "audit design" |
| **teach-impeccable** | 收集项目设计上下文并保存（首次使用其他技能前必须先运行） | "setup design context", "init design" |
| **normalize** | 规范化设计以匹配设计系统 | "normalize", "统一规范", "符合设计系统" |
| **arrange** | 优化布局、间距和视觉节奏 | "优化布局", "fix layout", "改进排版" |
| **typeset** | 改进字体选择、层次结构、可读性 | "typeset", "字体优化", "typography" |
| **colorize** | 为单调界面添加战略性颜色 | "添加颜色", "too monochrome", "颜色单调" |
| **animate** | 添加有目的的动画和微交互 | "添加动画", "make it animate", "动效优化" |
| **clarify** | 改进 UX 文案、错误消息、标签 | "优化文案", "fix copy", "改进微文案" |
| **harden** | 增强界面健壮性（错误处理、国际化、边缘情况） | "增加健壮性", "错误处理", "harden" |
| **adapt** | 适配不同屏幕尺寸和设备 | "适配移动端", "responsive", "响应式设计" |
| **bolder** | 增强视觉冲击力（适合保守设计） | "make this bolder", "增加视觉冲击力" |
| **quieter** | 降低过于强烈的视觉设计 | "quieter", "太强烈", "降低视觉强度" |
| **distill** | 简化设计，去除不必要的复杂性 | "simplify", "简化", "去除复杂度" |
| **delight** | 添加惊喜和愉悦的交互时刻 | "add delight", "增加惊喜", "提升体验" |
| **extract** | 提取可复用组件到设计系统 | "extract components", "提取组件", "设计系统" |
| **onboard** | 优化新用户引导和空状态 | "onboarding", "新用户引导", "empty state" |
| **optimize** | 性能优化（加载速度、渲染、动画） | "optimize", "性能优化", "加速" |
| **overdrive** | 技术突破（Shader、60fps 虚拟表格等） | "overdrive", "技术突破", "高级效果" |
| **polish** | 最终润色（对齐、间距、一致性检查） | "polish", "最终检查", "shipping前检查" |
| **critique** | 设计评估和反馈 | "评估设计", "critique this", "设计反馈" |
| **frontend-design** | 前端设计原则参考 | 需要设计指导时 |
| **webapp-testing** | 设置和运行 E2E 测试（Playwright） | "create E2E tests", "set up testing", "automated browser tests", "测试", "e2e" |

---

### 推荐优化调用顺序

当需要优化一个页面时，建议按以下顺序调用 Skills：

```
第一阶段：诊断和准备
├── 1. teach-impeccable         (首次使用 - 建立设计上下文)
├── 2. web-design-guidelines    (根据 Vercel Web Interface Guidelines 审查代码)
└── 3. audit                    (全面审查，发现问题)

第二阶段：结构性优化
├── 4. normalize                (规范化到设计系统)
├── 5. distill                  (简化不必要的复杂性)
└── 6. arrange                  (优化布局和间距) 

第三阶段：视觉优化
├── 7. typeset                  (优化字体排版)
├── 8. colorize                 (添加战略性颜色) //谨慎使用，避免过度设计
└── 9. bolder/quieter           (根据需要增强或降低视觉强度) //谨慎使用，避免过度设计

第四阶段：交互优化
├── 10. animate                 (添加动画和微交互)
├── 11. clarify                 (优化文案)
└── 12. delight                 (添加惊喜时刻)  //谨慎使用，避免过度设计

第五阶段：健壮性和适配
├── 13. harden                  (错误处理和边缘情况)
├── 14. adapt                   (响应式适配)
└── 15. onboard                 (优化空状态和引导)

第六阶段：最终交付
├── 16. extract                 (提取可复用组件)
├── 17. optimize                (性能优化)
└── 18. polish                  (最终润色)
```

---

### Skill 详细说明

#### 1. web-design-guidelines - Web Interface Guidelines 审查
**功能**：根据 Vercel 的 Web Interface Guidelines 审查 UI 代码合规性  
**工作原理**：
1. 从 GitHub 获取最新指南
2. 读取指定文件
3. 检查所有规则合规性
4. 以 `file:line` 格式输出发现的问题  
**使用场景**：需要专业、权威的 UI/UX 审查时  
**参数**：`<file-or-pattern>` - 要审查的文件或文件模式

#### 2. audit - 全面审查
**功能**：检查可访问性、性能、主题、响应式设计和反模式  
**输出**：详细的问题报告，包含严重等级和建议  
**使用场景**：开始优化前，或需要全面评估时

#### 3. teach-impeccable - 设计上下文设置
**功能**：收集项目设计上下文并保存到 `.impeccable.md`  
**注意**：首次使用其他设计技能前必须先运行  
**使用场景**：项目初始化，或设计方向发生变化时

#### 4. normalize - 规范化
**功能**：使设计匹配设计系统标准  
**处理内容**：字体、颜色、间距、组件、动画、响应式  
**使用场景**：确保设计一致性时

#### 5. arrange - 布局优化
**功能**：改进布局、间距和视觉节奏  
**解决**：单调网格、不一致间距、弱视觉层次  
**使用场景**：页面结构感觉"不对劲"时

#### 6. typeset - 字体优化
**功能**：改进字体选择、层次结构、可读性  
**避免**：使用过度使用的字体（Inter、Roboto、Arial）  
**使用场景**：文字看起来普通或难以阅读时

#### 7. colorize - 颜色优化
**功能**：为单调界面添加战略性颜色  
**原则**：更多颜色 ≠ 更好，每个颜色都应有目的  
**使用场景**：界面过于灰白或缺乏视觉兴趣时

#### 8. bolder - 视觉增强
**功能**：增强保守或无聊设计的视觉冲击力  
**警告**：避免 AI Slop（蓝紫渐变、玻璃拟态等）  
**使用场景**：设计过于安全、缺乏个性时

#### 9. quieter - 视觉降噪
**功能**：降低过于强烈或激进的视觉设计  
**原则**：精致 ≠ 无聊，通过克制传递品质感  
**使用场景**：设计过于花哨或令人疲劳时

#### 10. distill - 简化设计
**功能**：去除不必要的复杂性，揭示本质  
**原则**：简化 ≠ 功能缺失，而是去除障碍  
**使用场景**：界面感觉杂乱或过于复杂时

#### 11. animate - 动画增强
**功能**：添加有目的的动画和微交互  
**技术**：使用 transform 和 opacity（GPU 加速）  
**使用场景**：界面缺乏反馈或感觉生硬时

#### 12. clarify - 文案优化
**功能**：改进 UX 文案、错误消息、标签  
**原则**：清晰的文案帮助用户成功  
**使用场景**：用户反馈界面难以理解时

#### 13. delight - 惊喜设计
**功能**：添加愉悦时刻和个性  
**时机**：成功状态、空状态、加载状态、交互反馈  
**使用场景**：希望提升用户体验时

#### 14. harden - 健壮性增强
**功能**：错误处理、国际化、文本溢出、边缘情况  
**测试**：极端输入、错误场景、多语言  
**使用场景**：准备生产环境发布时

#### 15. adapt - 响应式适配
**功能**：适配不同屏幕尺寸和设备  
**策略**：Desktop→Mobile 单列布局，Mobile→Desktop 多列布局  
**使用场景**：需要支持多设备时

#### 16. extract - 组件提取
**功能**：提取可复用组件到设计系统  
**价值**：提高一致性，降低维护成本  
**使用场景**：发现重复模式，需要系统化时

#### 17. onboard - 引导优化
**功能**：优化新用户引导和空状态  
**原则**：展示而非讲述，尽快传递价值  
**使用场景**：用户反馈难以入门时

#### 18. optimize - 性能优化
**功能**：加载速度、渲染、动画、图片、包大小  
**技术**：图片优化、代码分割、懒加载  
**使用场景**：性能指标不达标时

#### 19. overdrive - 技术突破
**功能**：突破常规限制的高级效果  
**示例**：Shader、60fps 虚拟表格、弹簧物理动画  
**注意**：必须先向用户展示 2-3 个方向并获得确认  
**使用场景**：需要令人印象深刻的视觉效果时

#### 20. polish - 最终润色
**功能**：修复对齐、间距、一致性问题  
**时机**：功能完成后的最后一步  
**使用场景**：准备发布前的质量检查

#### 21. critique - 设计评估
**功能**：从 UX 角度评估设计效果  
**维度**：视觉层次、信息架构、情感共鸣  
**使用场景**：需要专业设计反馈时

#### 22. webapp-testing - E2E 测试
**功能**：设置和运行端到端测试  
**技术**：Playwright，支持 Chromium/Firefox/Safari/移动端  
**包含**：
- 测试框架安装和配置
- Page Object Model 模式
- 认证 Fixtures
- 用户流程测试
- 视觉回归测试
- CI/CD 集成（GitHub Actions）  
**使用场景**：需要自动化测试、回归测试、用户流程验证时

---

### 快速参考：常见问题对应的 Skill

| 问题 | 推荐 Skill |
|------|-----------|
| 需要权威的 UI/UX 审查 | web-design-guidelines |
| 页面看起来普通/像 AI 生成的 | bolder, colorize, typeset |
| 布局感觉"不对劲" | arrange, normalize |
| 文字难以阅读 | typeset |
| 颜色太单调 | colorize |
| 颜色太花哨 | quieter |
| 界面太复杂 | distill |
| 缺乏交互反馈 | animate |
| 文案令人困惑 | clarify |
| 需要支持手机 | adapt |
| 性能慢 | optimize |
| 准备发布 | polish, harden |
| 用户难以入门 | onboard |
| 代码重复太多 | extract |
| 需要自动化测试 | webapp-testing |
| 需要 E2E 测试 | webapp-testing |
| 需要回归测试 | webapp-testing |


# 只运行应用管理的功能测试
npx playwright test applications.spec.js --project=chromium --grep "功能测试"

# 只运行新增应用测试
npx playwright test applications.spec.js --project=chromium --grep "新增应用"

# 在 UI 模式下运行
npx playwright test applications.spec.js --ui