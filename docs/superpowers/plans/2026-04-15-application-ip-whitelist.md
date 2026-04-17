# Application IP Whitelist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为应用管理新增 IP 白名单字段，并在 OAuth2 `/token` 与 `/userinfo` 端点按应用白名单限制访问来源。

**Architecture:** 沿用现有应用管理链路，在 `Application` 模型中保存每个应用的 IP 白名单列表，API 和前端表单负责展示与编辑，OAuth2 API 负责提取真实客户端 IP，服务层集中执行白名单校验。白名单对 `public` 与 `confidential` 客户端都可配置，空列表表示不限制。

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/yweb ORM, Vue 3, Element Plus, pytest

---

### Task 1: 补应用管理 API 与服务层测试

**Files:**
- Modify: `tests/test_api/test_application_api.py`
- Modify: `tests/test_services/test_application_service.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run targeted pytest and confirm they fail because `allowed_ip_cidrs` 尚未透传/持久化**
- [ ] **Step 3: Implement minimal API DTO 与服务层存储逻辑**
- [ ] **Step 4: Re-run targeted pytest and confirm pass**

### Task 2: 补 OAuth2 白名单测试

**Files:**
- Modify: `tests/test_api/test_oauth2_provider_api.py`
- Modify: `tests/test_services/test_oauth2_provider_service.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run targeted pytest and confirm they fail because `/token` `/userinfo` 尚未执行 IP 白名单校验**
- [ ] **Step 3: Implement minimal IP 提取与服务校验逻辑**
- [ ] **Step 4: Re-run targeted pytest and confirm pass**

### Task 3: 更新前后端应用管理

**Files:**
- Modify: `app/domain/application/entities.py`
- Modify: `app/domain/application/services.py`
- Modify: `app/api/v1/application.py`
- Modify: `frontend/src/pages/applications/Index.vue`
- Create: `alembic/versions/<new migration>.py`

- [ ] **Step 1: 增加模型字段、校验方法与迁移**
- [ ] **Step 2: 在 API 请求/响应模型中暴露白名单字段**
- [ ] **Step 3: 在前端表单中增加多行输入、回填与提交逻辑**
- [ ] **Step 4: 验证应用管理链路**

### Task 4: 回归验证

**Files:**
- Modify: `app/api/v1/oauth2.py`

- [ ] **Step 1: 运行新增测试与相关既有测试**
- [ ] **Step 2: 检查最近编辑文件的 lints**
- [ ] **Step 3: 汇总剩余风险（代理配置、动态出口 IP、空白名单默认放行）**
