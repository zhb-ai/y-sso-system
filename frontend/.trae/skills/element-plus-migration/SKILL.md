---
name: "element-plus-migration"
description: "处理 Element Plus 组件库升级迁移问题。Invoke when user encounters Element Plus deprecation warnings, API changes, or version upgrade issues."
---

# Element Plus 迁移助手

此 skill 用于处理 Element Plus 组件库版本升级时的 API 变更和弃用警告。

## 常见问题

### 1. el-radio label 属性弃用 (v3.0.0+)

**问题**: `ElementPlusError: [el-radio] [API] label act as value is about to be deprecated in version 3.0.0, please use value instead.`

**解决方案**:
将 `:label` 改为 `:value`:

```vue
<!-- 错误 -->
<el-radio-group v-model="gender">
  <el-radio :label="0">未知</el-radio>
  <el-radio :label="1">男</el-radio>
  <el-radio :label="2">女</el-radio>
</el-radio-group>

<!-- 正确 -->
<el-radio-group v-model="gender">
  <el-radio :value="0">未知</el-radio>
  <el-radio :value="1">男</el-radio>
  <el-radio :value="2">女</el-radio>
</el-radio-group>
```

### 2. 检查项目中所有 el-radio

```bash
# 搜索所有使用 label 的 el-radio
grep -r "el-radio.*label" --include="*.vue" src/
```

### 3. 批量修复

使用 SearchReplace 工具批量替换:
- 搜索: `<el-radio :label="`
- 替换为: `<el-radio :value="`

## 迁移检查清单

- [ ] 检查所有 `el-radio` 组件的 `label` 属性
- [ ] 检查所有 `el-checkbox` 组件的 `label` 属性
- [ ] 检查 `el-option` 的 `label` vs `value` 使用
- [ ] 运行项目查看控制台是否有弃用警告
- [ ] 测试表单组件功能是否正常

## 参考链接

- [Element Plus 更新日志](https://github.com/element-plus/element-plus/blob/dev/CHANGELOG.en-US.md)
- [Element Plus 官方文档](https://element-plus.org/)
