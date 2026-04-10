---
name: "prevent-password-autofill"
description: "提供防止浏览器和密码管理器自动填充密码输入框的解决方案。当需要创建密码输入框或处理密码自动填充问题时调用此技能。"
---

# 防止密码自动填充解决方案

## 问题描述

浏览器和密码管理器（如 LastPass）会自动填充密码输入框，这在新建用户、重置密码等场景下会造成困扰。

## 解决方案

### Element Plus 密码输入框

对于 Element Plus 的 `el-input` 组件，使用以下属性组合：

```vue
<el-input
  v-model="password"
  type="password"
  placeholder="请输入密码"
  show-password
  autocomplete="new-password"
  :input-attrs="{ autocomplete: 'new-password', 'data-lpignore': 'true', 'data-form-type': 'other' }"
/>
```

### 属性说明

| 属性 | 值 | 作用 |
|------|-----|------|
| `autocomplete` | `new-password` | HTML5 标准属性，告诉浏览器这是新密码，不要使用已保存的密码填充 |
| `data-lpignore` | `true` | 阻止 LastPass 密码管理器自动填充 |
| `data-form-type` | `other` | 告诉浏览器这不是登录表单 |

### 不同场景的使用

#### 1. 新建用户/注册 - 新密码
```vue
<el-input
  v-model="form.password"
  type="password"
  placeholder="请输入初始密码"
  show-password
  autocomplete="new-password"
  :input-attrs="{ autocomplete: 'new-password', 'data-lpignore': 'true', 'data-form-type': 'other' }"
/>
```

#### 2. 登录页面 - 当前密码
```vue
<el-input
  v-model="form.password"
  type="password"
  placeholder="请输入密码"
  show-password
  autocomplete="current-password"
  :input-attrs="{ autocomplete: 'current-password' }"
/>
```

#### 3. 普通文本输入框（也建议添加防止填充）
```vue
<el-input
  v-model="form.username"
  placeholder="请输入用户名"
  autocomplete="off"
  :input-attrs="{ autocomplete: 'off', 'data-lpignore': 'true', 'data-form-type': 'other' }"
/>
```

### 原生 HTML 输入框

如果使用原生 HTML：

```html
<!-- 新密码 -->
<input
  type="password"
  name="new-password"
  autocomplete="new-password"
  data-lpignore="true"
  data-form-type="other"
/>

<!-- 当前密码 -->
<input
  type="password"
  name="current-password"
  autocomplete="current-password"
/>
```

## 注意事项

1. **新建密码场景**必须使用 `autocomplete="new-password"`，而不是 `autocomplete="off"`
2. **登录场景**使用 `autocomplete="current-password"` 允许浏览器填充
3. 对于密码管理器，添加 `data-lpignore="true"` 可以阻止 LastPass 等工具
4. `data-form-type="other"` 可以进一步防止浏览器识别为登录表单

## 参考

- [MDN: autocomplete 属性](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Attributes/autocomplete)
- [Element Plus Input 文档](https://element-plus.org/zh-CN/component/input.html)
