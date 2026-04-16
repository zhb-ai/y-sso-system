# Data Formulator 与 Superset 开发者对接说明

> 目标读者：`Data Formulator` 开发者、`Superset` 开发者、负责提供 SSO 参数的后端同学。
>
> 本文档只讲一件事：各项目里到底要改哪个文件、填什么值、在 SSO 后台要创建什么应用。

## 一、先看结论

建议在 `y-sso-system` 中创建两个独立客户端，不要共用：

- `Data Formulator`：`public` 客户端
- `Superset`：`confidential` 客户端

原因：

- `Data Formulator` 是前端 OIDC 登录场景，推荐 `public + PKCE`
- `Superset` 是服务端 OAuth/OIDC 场景，推荐 `confidential + client_secret`

## 二、SSO 侧先准备什么

这一部分通常由 `y-sso-system` 维护者完成。

### 1. SSO 配置文件

需要重点检查：

文件：`y-sso-system/config/settings.yaml`

最少确认这些配置：

```yaml
jwt:
  algorithm: RS256
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  refresh_token_sliding_days: 2

jwt_private_key_path: "config/dev-keys/jwt_private.pem"
jwt_public_key_path: "config/dev-keys/jwt_public.pem"
jwt_key_id: "sso-dev-rs256-key-1"

base_url: "http://localhost:8000"
oidc_issuer: "http://localhost:8000/api/v1/oauth2"
```

关键说明：

- `base_url`
  - 必须是下游系统真实访问到的 SSO 根地址
- `oidc_issuer`
  - 必须是下游配置中的 `OIDC_ISSUER_URL` / `issuer`
  - 默认建议配置为 `${base_url}/api/v1/oauth2`
  - 除了末尾 `/` 可忽略外，不要写成不同域名、不同端口或不同路径
- `jwt.algorithm`
  - 推荐 `RS256`
- `jwt_private_key_path` / `jwt_public_key_path`
  - 必须指向有效密钥文件

### 2. 在 SSO 后台创建 DF 应用

在 `y-sso-system` 管理后台的应用管理中创建：

| 配置项 | 建议值 |
|--------|--------|
| 应用名称 | `Data Formulator` |
| 客户端类型 | `public` |
| 是否启用 | `启用` |
| redirect_uris | `http://localhost:5567/callback` |

如果不是本地地址，替换成你的真实地址，例如：

```text
http://<df-host>:5567/callback
https://<df-domain>/callback
```

创建后提供给 DF 开发者：

- `client_id`
- `issuer`

说明：

- `DF` 场景通常不需要 `client_secret`
- 当前方案默认走 `PKCE(S256)`

### 3. 在 SSO 后台创建 Superset 应用

在 `y-sso-system` 管理后台的应用管理中再创建一个：

| 配置项 | 建议值 |
|--------|--------|
| 应用名称 | `Superset` |
| 客户端类型 | `confidential` |
| 是否启用 | `启用` |
| redirect_uris | `http://localhost:8088/oauth-authorized/y-sso` |

如果不是本地地址，替换成你的真实地址，例如：

```text
http://<superset-host>:8088/oauth-authorized/y-sso
https://<superset-domain>/oauth-authorized/y-sso
```

创建后提供给 Superset 开发者：

- `client_id`
- `client_secret`
- `issuer`

重要说明：

- 这个回调地址不是随便写的
- 当前 `superset-master/oauth_config.py` 中 provider 名称是 `y-sso`
- Flask AppBuilder 的回调路径格式是 `/oauth-authorized/<provider>`
- 所以默认必须是 `/oauth-authorized/y-sso`

如果你把 provider 名称改成别的，比如 `company-sso`，那么 SSO 里的回调地址也必须改成：

```text
/oauth-authorized/company-sso
```

### 4. SSO 维护者需要发给对接方哪些参数

最少需要发：

- `DF client_id`
- `Superset client_id`
- `Superset client_secret`
- `SSO issuer`

如果对方要核对协议端点，可以提供：

- `/api/v1/oauth2/.well-known/openid-configuration`
- `/api/v1/settings/oauth2-endpoints`

## 三、Data Formulator 开发者要改什么

以下路径基于当前工作区结构：

- `d:\Workspace\sso\data-formulator-dev`

### 1. 必改文件

文件：`data-formulator-dev/.env`

最小必改配置：

```env
AUTH_PROVIDER=oidc
OIDC_ISSUER_URL=http://localhost:8000/api/v1/oauth2
OIDC_CLIENT_ID=<SSO 为 Data Formulator 创建的 client_id>
ALLOW_ANONYMOUS=false
AUTH_DISPLAY_NAME=Y-SSO Login
```

每个变量的含义：

- `AUTH_PROVIDER=oidc`
  - 启用 OIDC 登录
- `OIDC_ISSUER_URL`
  - 填 SSO 的 `oidc_issuer`
  - 不要填成 `/token`、`/userinfo` 这种具体端点
- `OIDC_CLIENT_ID`
  - 填 SSO 中 `Data Formulator` 这个 `public` 客户端的 `client_id`
- `ALLOW_ANONYMOUS=false`
  - 关闭匿名访问
- `AUTH_DISPLAY_NAME`
  - 登录按钮显示文案，可按需修改

### 2. 不建议手工配置的项

当前接入 `y-sso-system` 时，不建议优先手工填这些：

```env
# OIDC_AUTHORIZE_URL=
# OIDC_TOKEN_URL=
# OIDC_USERINFO_URL=
# OIDC_JWKS_URL=
# OIDC_CLIENT_SECRET=
```

原因：

- 当前 SSO 已支持标准 Discovery
- `DF` 推荐使用 `public + PKCE`
- 因此通常只需要 `OIDC_ISSUER_URL + OIDC_CLIENT_ID`
- `OIDC_CLIENT_SECRET` 不应放在前端项目配置中

补充说明：

- 当前链路会基于 Discovery 自动走 `PKCE(S256)`
- `DF` 开发者通常不需要手工填写 `code_verifier` / `code_challenge`

### 3. DF 在 SSO 中要登记什么回调地址

需要在 SSO 后台登记：

```text
http://localhost:5567/callback
```

如果是你自己的环境，替换成：

```text
http://<df-host>:5567/callback
https://<df-domain>/callback
```

说明：

- 当前仓库中，`DF` 前端路由在 `data-formulator-dev/src/app/App.tsx` 里固定注册为 `path: "/callback"`
- 因此当前对接文档里统一按 `/callback` 处理，不建议在没改 DF 源码的前提下自定义成别的路径

### 4. 如果 DF 还要对接 Superset 插件

还是改 `data-formulator-dev/.env`，补充：

```env
PLG_SUPERSET_URL=http://localhost:8088
# 可选
# PLG_SUPERSET_SSO_LOGIN_URL=http://localhost:8088/login/?next=/df-sso-bridge/
```

说明：

- `PLG_SUPERSET_URL`
  - 填 Superset 根地址
- `PLG_SUPERSET_SSO_LOGIN_URL`
  - 可选
  - 如果你希望 DF 弹窗先进入 Superset 登录页再跳到 bridge，可以显式设置

### 5. DF 开发者最小修改清单

只看这一小段也能开工：

1. 找到 `data-formulator-dev/.env`
2. 设置：
   - `AUTH_PROVIDER=oidc`
   - `OIDC_ISSUER_URL=<SSO oidc_issuer>`
   - `OIDC_CLIENT_ID=<DF client_id>`
   - `ALLOW_ANONYMOUS=false`
3. 不要配置 `OIDC_CLIENT_SECRET`
4. 确保 SSO 后台已登记 `http://<df-host>:5567/callback`

## 四、Superset 开发者要改什么

以下路径基于当前工作区结构：

- `d:\Workspace\sso\superset-master`

Superset 侧至少要看两个文件：

- `superset-master/oauth_config.py`
- `superset-master/superset_config.py`

### 1. 改 `oauth_config.py`

文件：`superset-master/oauth_config.py`

这个文件里至少要改 4 处。

#### 1.1 改 `userinfo_url`

把：

```python
userinfo_url = 'http://localhost:8000/api/v1/oauth2/userinfo'
```

改成你的实际 SSO 地址，例如：

```python
userinfo_url = 'https://sso.example.com/api/v1/oauth2/userinfo'
```

#### 1.2 改 `role_mapping`

这里决定 SSO 角色如何映射到 Superset 本地角色：

```python
role_mapping = {
    'admin': 'Admin',
    'user': 'Gamma',
    's001': '管理员',
    's002': '数据分析师',
}
```

注意：

- 左边是 SSO 返回的角色编码
- 右边必须是 Superset 中真实存在的角色名
- 如果你们环境里的角色不是这些名字，请按真实角色名修改，不要直接照抄示例
- 当前 `oauth_config.py` 中实际优先读取 UserInfo 里的 `sso_roles` 字段；如果没有，才回退读取 `roles`

#### 1.3 改 OAuth 客户端参数

把 `OAUTH_CONFIG` 中 `remote_app` 这一段改成你的实际值：

```python
'remote_app': {
    'client_id': '<SSO 为 Superset 创建的 client_id>',
    'client_secret': '<SSO 为 Superset 创建的 client_secret>',
    'server_metadata_url': 'http://localhost:8000/api/v1/oauth2/.well-known/openid-configuration',
    'client_kwargs': {'scope': 'openid profile email'},
},
```

每项含义：

- `client_id`
  - 来自 SSO 后台 `Superset` 应用
- `client_secret`
  - 同样来自该应用
- `server_metadata_url`
  - 填 SSO 的 Discovery 地址
- `scope`
  - 建议保持 `openid profile email`

#### 1.4 不要随意改 provider 名称

当前配置里：

```python
'name': 'y-sso',
```

它直接影响回调地址：

```text
/oauth-authorized/y-sso
```

如果改名，比如改成：

```python
'name': 'company-sso',
```

那么 SSO 后台登记的 redirect URI 也必须同步改成：

```text
/oauth-authorized/company-sso
```

### 2. 确认 `superset_config.py`

文件：`superset-master/superset_config.py`

这个文件重点不是填地址，而是确认配置仍然生效。

#### 2.1 确认 OAuth 配置导入仍在

至少要保留：

```python
from oauth_config import OAUTH_CONFIG
globals().update(OAUTH_CONFIG)
```

如果这段没有生效，Superset 就不会启用 SSO 登录。

#### 2.2 如果还要给 DF 提供 bridge，确认 `SSOBridgeView` 注册仍在

如果你们除了 Superset 自己登录 SSO，还要支持 `DF -> Superset bridge`，那么还必须保留：

```python
from oauth_config import SSOBridgeView
appbuilder.add_view_no_menu(SSOBridgeView())
```

如果这段没生效：

- DF 无法通过 `/df-sso-bridge/` 拿到 Superset JWT
- DF 的 Superset 插件 SSO 登录链路会中断

也就是说：

- 只做 Superset 自己接入 SSO：`oauth_config.py` 是核心
- 还要支持 DF 通过 Superset bridge 获取 JWT：`superset_config.py` 里的 bridge 注册必须保留

### 3. Superset 在 SSO 中要登记什么回调地址

需要在 SSO 后台登记：

```text
http://localhost:8088/oauth-authorized/y-sso
```

如果是你自己的环境，替换成：

```text
http://<superset-host>:8088/oauth-authorized/y-sso
https://<superset-domain>/oauth-authorized/y-sso
```

### 4. Superset 开发者最小修改清单

只看这一小段也能开工：

1. 找到 `superset-master/oauth_config.py`
2. 修改：
   - `userinfo_url`
   - `role_mapping`
   - `client_id`
   - `client_secret`
   - `server_metadata_url`
3. 确认 provider 名称和 SSO 回调地址一致，默认是 `y-sso`
4. 找到 `superset-master/superset_config.py`
5. 确认 `OAUTH_CONFIG` 导入仍生效
6. 如果 DF 还要走 Superset bridge，确认 `SSOBridgeView` 注册仍在

## 五、三方联调建议顺序

1. SSO 维护者先在后台创建两个应用：`DF(public)`、`Superset(confidential)`。
2. 把 `DF client_id` 发给 DF 开发者。
3. 把 `Superset client_id/client_secret` 发给 Superset 开发者。
4. DF 开发者修改 `data-formulator-dev/.env`。
5. Superset 开发者修改 `superset-master/oauth_config.py`，并检查 `superset_config.py`。
6. 三方一起验证：
   - `DF -> SSO` 登录
   - `Superset -> SSO` 登录
   - `DF -> Superset bridge` 获取 Superset JWT

## 六、最容易遗漏的点

- 给 DF 和 Superset 共用了同一个客户端
- DF 误用了 `client_secret`
- Superset 的回调地址没有和 provider 名称对应
- SSO 的 `base_url` 仍然是 `localhost`，但下游用的是公网地址
- `role_mapping` 右侧填写了并不存在的 Superset 角色名
- `superset_config.py` 里的 `OAUTH_CONFIG` 导入或 `SSOBridgeView` 注册失效
