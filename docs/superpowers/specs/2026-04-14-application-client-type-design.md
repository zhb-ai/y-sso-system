# Application Client Type Design

**目标：** 为 `y-sso-system` 的应用管理补齐 `client_type` 的 UI/API 开关，让管理员可在新建和编辑应用时切换 `confidential` / `public`，并保证密钥行为与 OAuth2/PKCE 规则一致。

## 背景

当前 `Application` 领域模型和 `ApplicationService.create_application()` 已支持 `client_type` 字段，且 `OAuth2ProviderService` 已对 `public` 客户端启用 PKCE 校验。但应用管理页面、应用管理 API 的请求模型和响应 DTO 还未暴露该字段，导致管理员无法在管理端配置公开客户端。

## 设计决策

### UI 设计

- 在 `frontend/src/pages/applications/Index.vue` 的新建/编辑弹窗中新增 `客户端类型` 单选项：
  - `confidential`：机密客户端，使用 `client_secret`
  - `public`：公开客户端，不使用 `client_secret`，需要 PKCE
- 新建默认值为 `confidential`
- 编辑时回填当前值，并允许切换
- 选择 `public` 时展示辅助说明：公开客户端不使用客户端密钥，授权码流程需配合 PKCE
- 对接配置区域补充 `客户端类型` 展示，并让 PKCE 文案与 `public` 选择保持一致
- 创建成功或重置密钥时：
  - `confidential` 显示真实 `client_secret`
  - `public` 显示“无需密钥”或空字符串，不误导用户复制无效密钥

### API 契约

- `ApplicationResponse` 增加 `client_type`
- `CreateApplicationRequest` 增加 `client_type`，默认 `confidential`
- `UpdateApplicationRequest` 增加可选 `client_type`
- `POST /v1/applications/create` 把 `client_type` 传入服务层
- `POST /v1/applications/update` 允许更新 `client_type`

### 服务层行为

- `ApplicationService.create_application()` 继续使用现有 `client_type` 参数
- `ApplicationService.update_application()` 增加切换逻辑，保证密钥状态与客户端类型一致：
  - 切到 `public`：清空 `client_secret`
  - 切到 `confidential`：若当前 `client_secret` 为空，则生成新密钥
- `reset_client_secret()` 保持现有行为：
  - `public` 返回空密钥
  - `confidential` 生成并返回新密钥

## 错误处理

- API 层继续捕获 `ValueError` 并映射为 `Resp.BadRequest()` / `Resp.NotFound()`
- 对 `client_type` 使用枚举约束，非法值在请求模型阶段拦截

## 测试策略

- API 测试：
  - 创建接口能接收并返回 `client_type`
  - 更新接口能透传 `client_type`
- Service 测试：
  - 新建 `public` 客户端时不生成密钥
  - 从 `confidential` 切换到 `public` 时清空密钥
  - 从 `public` 切换到 `confidential` 时自动生成新密钥
- 回归关注：
  - 现有 OAuth2 public client + PKCE 相关测试继续通过

## 影响范围

- 后端：`app/api/v1/application.py`、`app/domain/application/services.py`
- 前端：`frontend/src/pages/applications/Index.vue`
- 测试：`tests/test_api/test_application_api.py`、新增应用服务测试文件
