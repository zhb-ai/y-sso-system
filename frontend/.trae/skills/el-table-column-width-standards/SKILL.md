---
name: "el-table-column-width-standards"
description: "Enforces el-table-column width standards: width must be >= label length * 40px. Invoke when reviewing table columns or user mentions table column width issues."
---

# Element Plus Table Column Width Standards

## Rule

For every `el-table-column` component with a `label` attribute and `width` attribute:

```
width >= label.length * 40
```

### Examples

| Label | Minimum Width | Current | Status |
|-------|--------------|---------|--------|
| 主组织 | 3 * 40 = 120 | 90 | ❌ Too small |
| 操作 | 2 * 40 = 80 | 160 | ✅ OK |
| 员工编码 | 4 * 40 = 160 | 120 | ❌ Too small |
| 雇佣状态 | 4 * 40 = 160 | 110 | ❌ Too small |
| 账号 | 2 * 40 = 80 | 90 | ✅ OK |

## Implementation

1. Calculate minimum width: `label字符数 * 40`
2. If current `width` < minimum, update to minimum
3. Use `min-width` for flexible columns that need to expand
4. Keep `width` for fixed-width columns

## Code Pattern

```vue
<!-- Before -->
<el-table-column label="主组织" width="90" align="center">

<!-- After -->
<el-table-column label="主组织" width="120" align="center">
```

## Exceptions

- Columns with `min-width` instead of `width` are flexible and don't need this rule
- `ID` column can use smaller width (typically 70-80)
- Operation columns (`操作`) may need extra width for multiple buttons
