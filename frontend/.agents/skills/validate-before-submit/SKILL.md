---
name: validate-before-submit
description: Enforce form validation before submit. Validate first, return early on failure, and only then run the async submit logic inside try/catch so validation errors aren’t swallowed and misreported.
user-invocable: true
argument-hint: [FORM_REF=<refVarName> SUBMIT_FN=<fnName>]
---

When implementing Element Plus / Vue forms that submit data (create/update/save), **always validate first** and **return early** on failure. Do **not** wrap the validation inside the same try/catch as the API call; otherwise validation throws may be caught and shown as “save failed”.

## Required Pattern (Vue 3 + Element Plus)

Use the exact flow below:

1. Ensure `formRef` exists (optional but recommended for async mounting).
2. Run validation and convert failures to `false`.
3. If not valid, `return` immediately.
4. Only then set loading and run the submit logic inside try/catch.

```js
if (!formRef.value) return

// Validate first. If invalid, stop here.
const isValid = await formRef.value.validate().catch(() => false)
if (!isValid) return

loading.value = true
try {
  await apiCall()
  // success message / refresh
} catch (e) {
  // handle submit errors (network/server)
} finally {
  loading.value = false
}
```

## Never Do This

- Don’t do `await formRef.value.validate()` inside the submit try/catch.
- Don’t show “保存失败/提交失败” for validation errors; validation should display field-level errors only.

## Local Reference (in this repo)

Follow the existing example in `src/pages/employees/Index.vue` around the submit handler validation flow.

