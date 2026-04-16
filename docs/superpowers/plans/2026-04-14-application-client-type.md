# Application Client Type Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为应用管理补齐 `client_type` 的前后端开关，并在切换客户端类型时保持客户端密钥状态正确。

**Architecture:** 沿用现有应用管理链路，在 API DTO 中暴露 `client_type`，在服务层集中处理类型切换后的密钥同步，在前端表单中增加一个单选字段并回填列表/编辑态数据。测试采用 TDD，先补 API 与服务层失败用例，再做最小实现，最后回归已有 OAuth2 public client 行为。

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/yweb Active Record, Vue 3, Element Plus, pytest

---

### Task 1: API 契约补齐

**Files:**
- Modify: `app/api/v1/application.py`
- Test: `tests/test_api/test_application_api.py`

- [ ] **Step 1: Write the failing test**

```python
def test_create_application_accepts_client_type(self, monkeypatch):
    """创建应用时应透传并返回 client_type"""


def test_update_application_accepts_client_type(self, monkeypatch):
    """更新应用时应透传 client_type"""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api/test_application_api.py -v`
Expected: FAIL，提示创建/更新接口未处理 `client_type`

- [ ] **Step 3: Write minimal implementation**

```python
class ApplicationResponse(DTO):
    client_type: str = "confidential"


class CreateApplicationRequest(BaseModel):
    client_type: Literal["confidential", "public"] = "confidential"


class UpdateApplicationRequest(BaseModel):
    client_type: Optional[Literal["confidential", "public"]] = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api/test_application_api.py -v`
Expected: PASS

### Task 2: 服务层切换逻辑

**Files:**
- Modify: `app/domain/application/services.py`
- Create: `tests/test_services/test_application_service.py`

- [ ] **Step 1: Write the failing test**

```python
def test_create_public_application_clears_secret():
    app = service.create_application(
        name="Public App",
        code="public_app",
        redirect_uris=["http://localhost/callback"],
        client_type="public",
    )
    assert app.client_type == "public"
    assert app.client_secret == ""


def test_update_application_to_public_clears_secret():
    updated = service.update_application(app.id, client_type="public")
    assert updated.client_secret == ""


def test_update_application_to_confidential_generates_secret_when_missing():
    updated = service.update_application(app.id, client_type="confidential")
    assert updated.client_type == "confidential"
    assert updated.client_secret
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_services/test_application_service.py -v`
Expected: FAIL，提示 `update_application()` 未同步处理密钥

- [ ] **Step 3: Write minimal implementation**

```python
if "client_type" in kwargs and kwargs["client_type"] != app.client_type:
    if kwargs["client_type"] == "public":
        kwargs["client_secret"] = ""
    elif kwargs["client_type"] == "confidential" and not app.client_secret:
        _, kwargs["client_secret"] = Application.generate_client_credentials()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_services/test_application_service.py -v`
Expected: PASS

### Task 3: 前端表单与展示补齐

**Files:**
- Modify: `frontend/src/pages/applications/Index.vue`

- [ ] **Step 1: Write the UI data flow change**

```javascript
const applicationForm = reactive({
  id: null,
  name: '',
  code: '',
  description: '',
  client_type: 'confidential',
  redirect_uris_str: '',
  logo_url: ''
})
```

- [ ] **Step 2: Add form control and payload mapping**

```vue
<el-form-item label="客户端类型" prop="client_type">
  <el-radio-group v-model="applicationForm.client_type">
    <el-radio value="confidential">机密客户端</el-radio>
    <el-radio value="public">公开客户端</el-radio>
  </el-radio-group>
</el-form-item>
```

- [ ] **Step 3: Wire create/update payloads and edit backfill**

```javascript
client_type: applicationForm.client_type
```

- [ ] **Step 4: Manual verification**

Run the app or review UI behavior to confirm:
- 新建默认 `confidential`
- 编辑可回填和切换
- `public` 文案显示“无需密钥 / 需 PKCE”

### Task 4: 回归验证

**Files:**
- Test: `tests/test_api/test_application_api.py`
- Test: `tests/test_services/test_application_service.py`
- Test: `tests/test_services/test_oauth2_provider_service.py`

- [ ] **Step 1: Run focused backend tests**

Run: `pytest tests/test_api/test_application_api.py tests/test_services/test_application_service.py tests/test_services/test_oauth2_provider_service.py -v`
Expected: PASS

- [ ] **Step 2: Check edited file diagnostics**

Run lints/diagnostics for:
- `app/api/v1/application.py`
- `app/domain/application/services.py`
- `frontend/src/pages/applications/Index.vue`

- [ ] **Step 3: Verify requirements coverage**

Checklist:
- 新建与编辑都可设置 `client_type`
- `public` 不暴露有效密钥
- `confidential` 可自动获得密钥
- 现有 public client + PKCE 行为不回退
