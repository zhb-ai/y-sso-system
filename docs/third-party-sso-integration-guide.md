# 第三方应用单点登录（SSO）技术对接指南

> **文档版本**：v1.0  
> **适用协议**：OAuth 2.0（RFC 6749）、PKCE（RFC 7636）、OpenID Connect Core 1.0、OpenID Connect Discovery 1.0、OAuth 2.0 Authorization Server Metadata（RFC 8414）、JSON Web Key（RFC 7517）、JSON Web Token（RFC 7519）  
> **目标读者**：第三方应用（依赖方）架构师、前后端研发工程师、系统集成工程师

---

## 目录

- [1. 概述](#1-概述)
  - [1.1 标准术语定义](#11-标准术语定义)
- [2. 接入准备与客户端选型](#2-接入准备与客户端选型)
  - [2.1 客户端类型选型](#21-客户端类型选型)
  - [2.2 应用注册与凭证获取](#22-应用注册与凭证获取)
  - [2.3 跨域资源共享（CORS）机制](#23-跨域资源共享cors机制)
- [3. 协议端点与服务发现](#3-协议端点与服务发现)
  - [3.1 自动发现（推荐）](#31-自动发现推荐)
  - [3.2 核心协议端点汇总](#32-核心协议端点汇总)
- [4. 交互时序与接入流程](#4-交互时序与接入流程)
  - [4.1 授权码模式完整时序图](#41-授权码模式完整时序图)
- [5. 接口规范（API Reference）](#5-接口规范api-reference)
  - [5.1 授权端点（Authorization Endpoint）](#51-授权端点authorization-endpoint)
  - [5.2 令牌端点（Token Endpoint）](#52-令牌端点token-endpoint)
  - [5.3 用户信息端点（UserInfo Endpoint）](#53-用户信息端点userinfo-endpoint)
  - [5.4 JSON Web Key Set 端点（JWKS Endpoint）](#54-json-web-key-set-端点jwks-endpoint)
- [6. 令牌结构与本地验签规范](#6-令牌结构与本地验签规范)
  - [6.1 凭证与令牌生命周期](#61-凭证与令牌生命周期)
  - [6.2 JWT Header 与 Payload 声明结构](#62-jwt-header-与-payload-声明结构)
  - [6.3 本地验签必检项（OIDC Core 1.0 §3.1.3.7）](#63-本地验签必检项oidc-core-10-3137)
  - [6.4 用户身份标识绑定规范](#64-用户身份标识绑定规范)
- [7. 代码集成示例](#7-代码集成示例)
  - [7.1 公开客户端：浏览器 SPA（TypeScript + PKCE S256）](#71-公开客户端浏览器-spatypescript--pkce-s256)
  - [7.2 机密客户端：服务端 Web 应用（Python + Authlib）](#72-机密客户端服务端-web-应用python--authlib)
  - [7.3 资源服务本地验签（Python + PyJWKClient）](#73-资源服务本地验签python--pyjwkclient)
- [8. 错误码与故障排查](#8-错误码与故障排查)
- [9. 安全基线与上线检查清单](#9-安全基线与上线检查清单)

---

## 1. 概述

单点登录系统作为企业统一身份提供商（Identity Provider, IdP）与授权服务器（Authorization Server），基于标准 **OAuth 2.0** 与 **OpenID Connect (OIDC) 1.0** 协议对外提供统一身份认证（Authentication）与授权码交换服务。

第三方业务系统作为依赖方（Relying Party, RP），通过接入本平台即可完成终端用户身份认证、令牌验签及组织架构扩展属性获取，无需在业务系统内维护用户凭证。

### 1.1 标准术语定义

本文档严格采用 IETF 与 OpenID Foundation 行业标准术语：

| 术语 | 英文全称 / 规范标识 | 定义与说明 |
| :--- | :--- | :--- |
| **身份提供商 / 授权服务器** | Identity Provider (IdP) / Authorization Server | 本单点登录系统。负责验证终端用户身份，并向依赖方签发授权码、访问令牌与身份令牌。 |
| **依赖方 / 客户端** | Relying Party (RP) / Client | 接入本系统的第三方业务应用。依赖 IdP 完成用户身份认证并消费令牌声明。 |
| **终端用户** | End-User / Resource Owner | 使用浏览器或客户端访问第三方业务应用的自然人用户。 |
| **用户代理** | User-Agent | 终端用户使用的浏览器或 WebView 容器，负责承载前端通道的 HTTP 重定向。 |
| **机密客户端** | Confidential Client | 具备安全服务端环境、能够安全存储 `client_secret` 且不向用户代理暴露密钥的客户端（如传统服务端 Web 应用、BFF 架构应用）。 |
| **公开客户端** | Public Client | 运行于用户代理或终端设备、无法安全保存 `client_secret` 的客户端（如纯浏览器单页应用 SPA、原生移动应用、桌面客户端）。 |
| **前端通道** | Front-Channel | 通过用户代理（浏览器地址栏重定向）在依赖方与授权服务器之间传递消息的通信链路。 |
| **后端通道** | Back-Channel | 依赖方后端服务与授权服务器之间直接建立的 TLS/HTTPS 服务端到服务端通信链路。 |
| **PKCE** | Proof Key for Code Exchange (RFC 7636) | 授权码交换证明密钥。通过动态生成的 `code_verifier` 与 `code_challenge` 防止授权码被拦截或重放。 |
| **签发者标识符** | Issuer Identifier (`issuer` / `iss`) | 唯一标识授权服务器的 URL。用于 OIDC 自动发现及 JWT `iss` 声明校验。 |
| **主体标识符** | Subject Identifier (`sub`) | 终端用户在当前 IdP 下的全局唯一、不可变标识符。 |
| **JSON Web Key Set** | JWKS (RFC 7517) | 授权服务器对外暴露的公钥集合，供依赖方在本地对 `id_token` 和 `access_token` 执行非对称数字签名校验。 |

---

## 2. 接入准备与客户端选型

### 2.1 客户端类型选型

依赖方在接入前，必须根据应用架构选择对应的客户端类型（`client_type`）。不同架构的客户端应注册为独立的应用实例，禁止多个业务系统共用同一 `client_id`。

| 维度 | 机密客户端 (`confidential`) | 公开客户端 (`public`) |
| :--- | :--- | :--- |
| **典型应用形态** | 传统服务端渲染 Web 应用、具备后端服务（BFF）的前后端分离应用 | 纯浏览器单页应用（SPA）、移动端 App（iOS/Android）、桌面客户端（Electron 等） |
| **令牌交换发起方** | 依赖方后端服务（通过后端通道调用 `/token`） | 浏览器前端或原生客户端直接调用 `/token` |
| **客户端密钥 (`client_secret`)** | **必须使用**。由服务端安全存储，严禁硬编码于前端代码或客户端安装包中。 | **不使用**。系统不分配 `client_secret`。 |
| **PKCE (`S256`)** | 可选支持（推荐启用；若授权请求携带 `code_challenge`，则换取令牌时必须校验 `code_verifier`）。 | **强制要求**。未携带 `code_challenge` 或算法非 `S256` 的请求将被直接拒绝。 |
| **后端通道 IP 白名单** | 推荐配置应用服务器出口 IP / CIDR。 | 通常不配置（请求来源于终端用户网络）。 |

### 2.2 应用注册与凭证获取

集成前，请联系 SSO 平台管理员在「应用管理」控制台完成客户端注册，并向管理员提供以下登记信息：

1. **应用名称与编码**：业务系统的显示名称与唯一英文标识（`code`）。
2. **客户端类型**：`confidential` 或 `public`。
3. **重定向 URI 列表（`redirect_uris`）**：接收授权码的完整回调地址（如 `https://app.example.com/oauth/callback`）。
   - 协议、域名、端口与路径必须与授权请求中的 `redirect_uri` 参数**精确匹配**（Exact Match）。
   - 生产环境必须使用 `https://` 协议。
4. **IP 白名单（`allowed_ip_cidrs`，可选）**：允许访问 `/token` 与 `/userinfo` 后端通道端点的客户端服务器 IP 地址或 CIDR 网段（如 `10.20.0.0/16`、`192.168.1.100`）。留空表示不限制来源 IP。

注册完成后，依赖方将从 SSO 管理台「对接信息」面板获取以下配置参数：

- `issuer`：OIDC 签发者标识符（格式为 `https://<sso-domain>/api/v1/oauth2`）
- `discovery_url`：OIDC 自动发现文档地址
- `client_id`：客户端唯一标识
- `client_secret`：客户端密钥（仅 `confidential` 客户端提供）

### 2.3 跨域资源共享（CORS）机制

针对公开客户端（如 SPA）通过浏览器直接请求 `/token`、`/userinfo`、`/.well-known/openid-configuration` 或 `/jwks` 的场景：

- SSO 平台内置动态 CORS 中间件，自动提取所有**已启用**应用的 `redirect_uris` 中的源（`<scheme>://<host>[:<port>]`）并加入 `Access-Control-Allow-Origin` 白名单。
- 应用新增或修改 `redirect_uris` 后，CORS 白名单缓存刷新周期最长为 **300 秒（5 分钟）**。
- 开发环境下默认放行 `http://localhost:*` 与 `http://127.0.0.1:*`。

---

## 3. 协议端点与服务发现

假设 SSO 平台对外访问根地址（`base_url`）为 `https://sso.example.com`，默认签发者标识符（`oidc_issuer`）为：

```text
https://sso.example.com/api/v1/oauth2
```

### 3.1 自动发现（推荐）

本平台实现 **OpenID Connect Discovery 1.0** 与 **RFC 8414** 标准。凡使用标准 OIDC/OAuth 2.0 SDK（如 `openid-client`、`Authlib`、`Spring Security OAuth2`、`oidc-client-ts`）的依赖方，应优先通过配置 `issuer` 或 `discovery_url` 自动加载协议元数据，无需硬编码各端点地址。

- **OIDC Discovery 端点**：`GET /api/v1/oauth2/.well-known/openid-configuration`
- **OAuth 2.0 元数据端点**：`GET /api/v1/oauth2/.well-known/oauth-authorization-server`

> **注意**：Discovery 端点挂载于 Issuer 路径前缀 `/api/v1/oauth2` 下，根路径 `/.well-known/openid-configuration` 不对外提供服务（返回 `404 Not Found`）。

**响应示例（`200 OK`）**：

```json
{
  "issuer": "https://sso.example.com/api/v1/oauth2",
  "authorization_endpoint": "https://sso.example.com/api/v1/oauth2/authorize",
  "token_endpoint": "https://sso.example.com/api/v1/oauth2/token",
  "userinfo_endpoint": "https://sso.example.com/api/v1/oauth2/userinfo",
  "jwks_uri": "https://sso.example.com/api/v1/oauth2/jwks",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "scopes_supported": ["openid", "profile", "email"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "code_challenge_methods_supported": ["S256"]
}
```

### 3.2 核心协议端点汇总

若依赖方不支持自动发现，可按以下完整路径手动配置各协议端点：

| 端点名称 | HTTP 方法与路径 | 通道类型 | 认证方式 | 用途说明 |
| :--- | :--- | :--- | :--- | :--- |
| **Discovery Endpoint** | `GET /api/v1/oauth2/.well-known/openid-configuration` | 公开 | 无需认证 | 获取 OIDC Provider 元数据配置 |
| **Authorization Endpoint** | `GET /api/v1/oauth2/authorize` | 前端通道 | 终端用户会话 | 发起授权请求，引导用户登录并签发一次性授权码 `code` |
| **Token Endpoint** | `POST /api/v1/oauth2/token` | 后端通道 | `client_secret_basic` / `client_secret_post` / PKCE | 使用授权码换取令牌，或使用 `refresh_token` 刷新令牌 |
| **UserInfo Endpoint** | `GET /api/v1/oauth2/userinfo` | 后端通道 | `Bearer <access_token>` | 获取当前授权用户的标准身份声明与组织扩展声明 |
| **JWKS Endpoint** | `GET /api/v1/oauth2/jwks` | 公开 | 无需认证 | 获取 RS256 签名公钥集，用于本地验签 `id_token` 与 `access_token` |

---

## 4. 交互时序与接入流程

本平台采用标准 **授权码模式（Authorization Code Flow）**，并支持 **PKCE（RFC 7636）** 扩展。

### 4.1 授权码模式完整时序图

```mermaid
sequenceDiagram
    autonumber
    actor User as 终端用户 (End-User)
    participant UA as 用户代理 (Browser)
    participant RP as 依赖方 (Relying Party)
    participant IdP as 授权服务器 (SSO IdP)

    User->>UA: 访问依赖方受保护资源
    UA->>RP: 发起访问请求（无本地会话）
    RP->>RP: 生成随机 state、nonce<br/>（若启用 PKCE，生成 code_verifier 与 code_challenge）
    RP-->>UA: 302 重定向至 IdP 授权端点 (/api/v1/oauth2/authorize)
    UA->>IdP: GET /api/v1/oauth2/authorize?response_type=code&client_id=...

    alt 终端用户在 IdP 已存在有效会话
        IdP->>IdP: 校验客户端、redirect_uri 及 PKCE 参数，自动签发授权码 code
    else 终端用户在 IdP 未登录
        IdP-->>UA: 302 重定向至统一登录页 (/sso/login)
        User->>IdP: 输入账号密码或使用企业微信扫码完成认证
        IdP->>IdP: 认证通过，签发一次性授权码 code（有效期 5 分钟）
    end

    IdP-->>UA: 302 重定向至 redirect_uri?code=AUTH_CODE&state=STATE
    UA->>RP: 请求回调地址并携带 code 与 state
    RP->>RP: 校验 state 与会话中保存的值一致（防 CSRF）

    RP->>IdP: POST /api/v1/oauth2/token<br/>(grant_type=authorization_code, code, redirect_uri, client_secret / code_verifier)
    IdP->>IdP: 校验客户端凭证、IP 白名单、code 单次有效性、redirect_uri 与 PKCE
    IdP-->>RP: 200 OK 返回 access_token, refresh_token, id_token, expires_in

    opt 本地验签与获取扩展用户信息
        RP->>IdP: GET /api/v1/oauth2/jwks（首次加载或 kid 未命中缓存时拉取）
        IdP-->>RP: 200 OK 返回 RSA 公钥集 (JWKS)
        RP->>RP: 使用 JWKS 公钥本地校验 id_token 签名、iss、aud、exp、nonce
        RP->>IdP: GET /api/v1/oauth2/userinfo (Authorization: Bearer <access_token>)
        IdP-->>RP: 200 OK 返回用户标准声明与企业组织角色声明 (sub, sso_roles, ...)
    end

    RP->>RP: 基于 sub 绑定或创建本地会话
    RP-->>UA: 下发依赖方应用会话凭证，展示业务页面
```

---

## 5. 接口规范（API Reference）

### 5.1 授权端点（Authorization Endpoint）

终端用户访问依赖方受保护页面且未登录时，依赖方通过用户代理（浏览器）将用户 `302` 重定向至该端点。

- **请求路径**：`GET /api/v1/oauth2/authorize`
- **通道类型**：前端通道（浏览器页面跳转，禁止使用 AJAX/Fetch 异步调用）

#### 请求参数（Query Parameters）

| 参数名 | 类型 | 必填 | 约束与说明 |
| :--- | :--- | :--- | :--- |
| `response_type` | `string` | 是 | 固定取值 `code`。表示使用授权码模式。 |
| `client_id` | `string` | 是 | 应用注册时分配的客户端唯一标识。 |
| `redirect_uri` | `string` | 是 | 授权成功后的回调 URI，须进行 URL 编码，且必须与应用注册的 `redirect_uris` 列表中的某一项精确匹配。 |
| `scope` | `string` | 否 | 以空格分隔的权限范围列表。支持 `openid`、`profile`、`email`。**若需获取 `id_token`，必须包含 `openid`**（推荐传 `openid profile email`）。 |
| `state` | `string` | 强烈推荐 | 依赖方生成的不可预测随机字符串，用于防御跨站请求伪造（CSRF）攻击。授权服务器会在重定向回 `redirect_uri` 时原样回传该参数。 |
| `nonce` | `string` | 推荐 | 依赖方生成的随机字符串，用于关联客户端会话与 `id_token`，防御重放攻击（Replay Attack）。当 `scope` 包含 `openid` 时，该值将原样写入 `id_token` 的 `nonce` 声明中。 |
| `code_challenge` | `string` | 条件必填 | PKCE 质询码。`public` 客户端**必填**；`confidential` 客户端可选。 |
| `code_challenge_method` | `string` | 条件必填 | PKCE 摘要算法。当传入 `code_challenge` 时**必填**，仅支持 `S256`（不支持 `plain`）。 |

#### PKCE 派生算法规范（RFC 7636）

1. **生成 `code_verifier`**：客户端生成高熵加密随机字符串，字符集限于 `[A-Z]`、`[a-z]`、`[0-9]`、`-`、`.`、`_`、`~`，长度介于 43 至 128 个字符之间。
2. **计算 `code_challenge`（`S256`）**：对 `code_verifier` 的 ASCII 字节流计算 SHA-256 哈希摘要，并进行无填充（去掉末尾 `=`）的 Base64URL 编码：
   ```text
   code_challenge = BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
   ```

#### 请求示例

```http
GET /api/v1/oauth2/authorize?response_type=code&client_id=nqB6VTGmZM49KvoxPqb4j&redirect_uri=https%3A%2F%2Fapp.example.com%2Foauth%2Fcallback&scope=openid%20profile%20email&state=xyz987654321&nonce=n-0S6_WzA2Mj&code_challenge=E9Melhoa2OwvFrGMTJgu...&code_challenge_method=S256 HTTP/1.1
Host: sso.example.com
```

#### 响应说明

1. **参数校验成功**：
   - 用户已完成认证后，授权服务器返回 `302 Found`，将浏览器重定向至 `redirect_uri` 并附带 `code` 与 `state` 参数：
     ```http
     HTTP/1.1 302 Found
     Location: https://app.example.com/oauth/callback?code=4b8e2f9a1c...&state=xyz987654321
     ```
2. **参数校验失败（如 `client_id` 不存在、`redirect_uri` 未登记、PKCE 参数缺失）**：
   - 为防止开放重定向漏洞（Open Redirect），授权服务器**不会**重定向至未经验证的 `redirect_uri`，而是直接返回 `400 Bad Request`：
     ```json
     {
       "error": "invalid_request",
       "error_description": "重定向URI无效: https://untrusted.example.com/callback"
     }
     ```

---

### 5.2 令牌端点（Token Endpoint）

依赖方使用一次性授权码 `code` 换取令牌，或使用 `refresh_token` 续期访问令牌。

- **请求路径**：`POST /api/v1/oauth2/token`
- **请求头**：`Content-Type: application/x-www-form-urlencoded`
- **通道类型**：后端通道（支持应用级 IP 白名单校验）

#### 客户端认证方式

令牌端点支持以下客户端认证方式（若请求同时携带 HTTP Basic 认证头与表单凭证，优先读取 HTTP Basic 认证头）：

1. **`client_secret_basic`（推荐，适用于机密客户端）**：
   在 HTTP 请求头中携带 `Authorization: Basic <base64(client_id:client_secret)>`。
2. **`client_secret_post`（适用于机密客户端）**：
   在 `application/x-www-form-urlencoded` 表单请求体中传递 `client_id` 与 `client_secret` 字段。
3. **无密钥 + PKCE（适用于公开客户端）**：
   在表单请求体中传递 `client_id` 与 `code_verifier`，不传递 `client_secret`。

---

#### 场景一：授权码换取令牌（`grant_type=authorization_code`）

##### 请求参数（Form Parameters）

| 参数名 | 类型 | 必填 | 约束与说明 |
| :--- | :--- | :--- | :--- |
| `grant_type` | `string` | 是 | 固定取值 `authorization_code`。 |
| `code` | `string` | 是 | 从授权端点回调中获取的一次性授权码。有效期 **5 分钟**，仅可使用一次。 |
| `redirect_uri` | `string` | 是 | 必须与请求 `/authorize` 时传入的 `redirect_uri` 完全一致。 |
| `client_id` | `string` | 条件必填 | 客户端 ID。当未使用 `client_secret_basic` 请求头时必填。 |
| `client_secret` | `string` | 条件必填 | 客户端密钥。`confidential` 客户端且未使用 `client_secret_basic` 请求头时必填；`public` 客户端不传。 |
| `code_verifier` | `string` | 条件必填 | PKCE 原始验证码。`public` 客户端**必填**；若 `confidential` 客户端在 `/authorize` 阶段传入了 `code_challenge`，此处也**必填**。 |

##### 请求示例（机密客户端）

```bash
curl -X POST "https://sso.example.com/api/v1/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "nqB6VTGmZM49KvoxPqb4j:pQm_ZXUQFo3wjgQXxMOuHuB5jlWN" \
  -d "grant_type=authorization_code" \
  -d "code=4b8e2f9a1c7d6e5f..." \
  -d "redirect_uri=https://app.example.com/oauth/callback"
```

##### 请求示例（公开客户端 + PKCE）

```bash
curl -X POST "https://sso.example.com/api/v1/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=df_public_client_id" \
  -d "code=4b8e2f9a1c7d6e5f..." \
  -d "redirect_uri=https://spa.example.com/callback" \
  -d "code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
```

##### 响应参数（`200 OK`）

| 字段名 | 类型 | 必返 | 说明 |
| :--- | :--- | :--- | :--- |
| `access_token` | `string` | 是 | 访问令牌（JWT 格式），用于调用 `/userinfo` 端点或由依赖方本地验签。 |
| `token_type` | `string` | 是 | 令牌类型，固定为 `"bearer"`。 |
| `expires_in` | `integer` | 是 | `access_token` 的有效时长（单位：秒，默认生产配置为 `1800`，即 30 分钟）。 |
| `refresh_token` | `string` | 是 | 刷新令牌（JWT 格式），用于在不打扰用户的情况下换取新的 `access_token`。 |
| `scope` | `string` | 是 | 实际授权的权限范围字符串（无指定时为 `""`）。 |
| `id_token` | `string` | 条件返回 | OIDC 身份令牌（JWT 格式）。**仅当授权请求的 `scope` 包含 `openid` 时返回**。 |

##### 响应示例

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6InNzby1yc2EyNTYta2V5LTEiLCJ0eXAiOiJKV1QifQ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6InNzby1yc2EyNTYta2V5LTEiLCJ0eXAiOiJKV1QifQ...",
  "scope": "openid profile email",
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6InNzby1yc2EyNTYta2V5LTEiLCJ0eXAiOiJKV1QifQ..."
}
```

---

#### 场景二：刷新访问令牌（`grant_type=refresh_token`）

当 `access_token` 即将过期或已过期时，依赖方可使用有效的 `refresh_token` 获取新的 `access_token` 与 `id_token`。

##### 请求参数（Form Parameters）

| 参数名 | 类型 | 必填 | 约束与说明 |
| :--- | :--- | :--- | :--- |
| `grant_type` | `string` | 是 | 固定取值 `refresh_token`。 |
| `refresh_token` | `string` | 是 | 之前签发的有效刷新令牌。 |
| `client_id` | `string` | 条件必填 | 客户端 ID。未使用 `client_secret_basic` 请求头时必填。 |
| `client_secret` | `string` | 条件必填 | 客户端密钥。`confidential` 客户端且未使用 `client_secret_basic` 请求头时必填；`public` 客户端不传。 |

##### 请求示例

```bash
curl -X POST "https://sso.example.com/api/v1/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "nqB6VTGmZM49KvoxPqb4j:pQm_ZXUQFo3wjgQXxMOuHuB5jlWN" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=eyJhbGciOiJSUzI1NiIs..."
```

##### 响应说明与滑动过期机制

- 接口固定返回新的 `access_token`、`token_type` (`"bearer"`)、`expires_in` 与 `id_token`。
- **滑动续期机制（Sliding Expiration）**：`refresh_token` 默认有效期为 **7 天**，滑动续期阈值为 **2 天**。当请求刷新时，若当前 `refresh_token` 剩余有效期小于或等于滑动阈值（2 天），响应中将额外返回签发的新 `refresh_token`，依赖方收到后应覆盖本地存储的旧 `refresh_token`。

---

### 5.3 用户信息端点（UserInfo Endpoint）

依赖方使用有效的 `access_token` 获取当前登录用户的标准身份信息、SSO 角色及组织架构扩展属性。

- **请求路径**：`GET /api/v1/oauth2/userinfo`
- **认证请求头**：`Authorization: Bearer <access_token>`
- **通道类型**：后端通道（支持应用级 IP 白名单校验）

#### 请求示例

```bash
curl -X GET "https://sso.example.com/api/v1/oauth2/userinfo" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..."
```

#### 响应字段说明（`200 OK`）

UserInfo 响应同时包含 **OIDC 标准声明（Standard Claims）** 与 **企业组织扩展声明（Enterprise Extension Claims）**：

| 字段名 | 类型 | 类别 | 必返 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `sub` | `string` | OIDC 标准 | 是 | **用户唯一不可变标识**（系统用户主键的字符串形式，如 `"42"`）。与 `id_token`、`access_token` 中的 `sub` 严格一致。 |
| `preferred_username` | `string \| null` | OIDC 标准 | 是 | 用户登录账号名（同步自企业微信时对应企业微信成员 `userid`）。仅供界面展示或辅助检索，不可作为不可变主键。 |
| `name` | `string` | OIDC 标准 | 是 | 用户姓名或显示名称。 |
| `email` | `string \| null` | OIDC 标准 | 是 | 用户电子邮箱地址（未设置时为 `null`）。 |
| `phone_number` | `string \| null` | OIDC 标准 | 是 | 用户手机号码（未设置时为 `null`）。 |
| `active` | `boolean` | OIDC 标准 | 是 | 账号激活状态（正常状态固定为 `true`；已禁用用户无法通过令牌校验）。 |
| `sso_roles` | `string[]` | 企业扩展 | 是 | **跨系统 SSO 角色编码列表**（如 `["s001", "data_analyst"]`）。推荐第三方应用优先读取该字段进行本地 RBAC 角色映射。 |
| `roles` | `string[]` | 企业扩展 | 是 | 用户在 SSO 平台内部的角色编码列表（如 `["admin", "internal_employee"]`）。 |
| `user_code` | `string` | 企业扩展 | 条件返回 | 关联员工工号/编码。仅当该用户已关联员工档案且员工编码非空时返回该字段。 |
| `enterprise_wechat_user_id` | `string \| null` | 企业扩展 | 是 | 关联的企业微信成员 `userid`（未绑定企业微信时为 `null`）。 |
| `emp_status` | `integer \| null` | 企业扩展 | 是 | 员工在职状态枚举：`-1` 离职、`0` 待入职、`1` 试用、`2` 实习、`3` 正式；未关联组织关系时为 `null`。 |
| `primary_external_dept_id` | `string \| null` | 企业扩展 | 是 | 员工主部门对应的外部（企业微信）部门 ID；未关联时为 `null`。 |
| `external_dept_ids` | `string[]` | 企业扩展 | 是 | 员工在主组织下所属的全部外部（企业微信）部门 ID 列表（若存在主部门则排在首位，已去重；无部门时为 `[]`）。 |
| `post_name` | `string \| null` | 企业扩展 | 是 | 员工在主组织中的职位/岗位名称；未设置时为 `null`。 |

#### 响应示例

```json
{
  "sub": "108",
  "preferred_username": "zhangsan",
  "name": "张三",
  "email": "zhangsan@example.com",
  "phone_number": "13800138000",
  "active": true,
  "roles": ["internal_employee"],
  "sso_roles": ["bi_analyst", "report_viewer"],
  "user_code": "EMP20260108",
  "enterprise_wechat_user_id": "zhangsan",
  "emp_status": 3,
  "primary_external_dept_id": "102",
  "external_dept_ids": ["102", "105"],
  "post_name": "高级数据分析师"
}
```

---

### 5.4 JSON Web Key Set 端点（JWKS Endpoint）

提供遵循 RFC 7517 规范的 RSA 公钥集合，供依赖方在本地验证 `id_token` 与 `access_token` 的 RS256 数字签名。

- **请求路径**：`GET /api/v1/oauth2/jwks`
- **通道类型**：公开端点（支持服务器拉取与浏览器跨域访问）

#### 响应示例（`200 OK`）

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "sso-rs256-key-1",
      "use": "sig",
      "alg": "RS256",
      "n": "x8f9d2a1b4c3...",
      "e": "AQAB"
    }
  ]
}
```

#### 公钥缓存与轮换建议

1. 依赖方应在内存或分布式缓存中缓存 `/jwks` 响应，禁止在每次业务请求中同步拉取公钥。
2. 当收到的 JWT Header 中的 `kid` 在本地缓存的 JWKS 中未命中时，依赖方应主动触发一次 JWKS 刷新（建议设置最小刷新间隔如 60 秒，防止恶意伪造 `kid` 引发回源风暴）。

---

## 6. 令牌结构与本地验签规范

### 6.1 凭证与令牌生命周期

| 凭证 / 令牌类型 | 格式 | 默认有效期 | 使用次数限制 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **授权码 (`code`)** | 高熵随机字符串 | 5 分钟 | **单次有效** | 兑换令牌后立即标记为已使用，重复使用将返回 `invalid_grant`。 |
| **访问令牌 (`access_token`)** | JWT (`RS256`) | 30 分钟 | 有效期内可多次使用 | 用于请求 `/userinfo` 端点或交由依赖方后端本地验签。 |
| **身份令牌 (`id_token`)** | JWT (`RS256`) | 30 分钟 | 供依赖方验证用户身份 | 遵循 OIDC Core 1.0 规范，包含用户核心身份声明。 |
| **刷新令牌 (`refresh_token`)** | JWT (`RS256`) | 7 天（滑动续期阈值 2 天） | 有效期内可刷新访问令牌 | 剩余有效期不足 2 天时，调用 `/token` 刷新将签发新的 `refresh_token`。 |

### 6.2 JWT Header 与 Payload 声明结构

#### JWT Header

```json
{
  "alg": "RS256",
  "kid": "sso-rs256-key-1",
  "typ": "JWT"
}
```

#### `id_token` 与 `access_token` Payload 声明对比

| 声明 (Claim) | 类型 | `id_token` | `access_token` | 说明 |
| :--- | :--- | :---: | :---: | :--- |
| `iss` | `string` | 包含 | 包含 | 签发者标识符，等于 SSO 配置的 `oidc_issuer`（如 `https://sso.example.com/api/v1/oauth2`）。 |
| `sub` | `string` | 包含 | 包含 | 用户唯一不可变标识（如 `"108"`）。 |
| `aud` | `string` | 包含 | 包含 | 受众标识，固定为当前客户端的 `client_id`。 |
| `iat` | `integer` | 包含 | 包含 | 签发时间（Unix 秒级时间戳）。 |
| `exp` | `integer` | 包含 | 包含 | 过期时间（Unix 秒级时间戳）。 |
| `name` | `string` | 包含 | 不包含 | 用户姓名（无姓名时回退为 `username`）。 |
| `preferred_username` | `string \| null` | 包含 | 不包含 | 用户登录名。 |
| `email` | `string \| null` | 包含 | 包含 | 用户邮箱地址。 |
| `nonce` | `string` | 条件包含 | 不包含 | 授权请求传入 `nonce` 时原样写入，用于防重放校验。 |
| `user_id` | `integer` | 不包含 | 包含 | 用户数字主键（与 `sub` 数值一致）。 |
| `username` | `string \| null` | 不包含 | 包含 | 用户登录名（与 `preferred_username` 值一致）。 |
| `roles` | `string[]` | 不包含 | 包含 | SSO 内部角色编码列表。 |
| `token_type` | `string` | 不包含 | 包含 | 固定为 `"access"`（刷新令牌中为 `"refresh"`）。 |

### 6.3 本地验签必检项（OIDC Core 1.0 §3.1.3.7）

依赖方在本地验证 `id_token` 或 `access_token` 时，必须依次执行以下校验步骤：

1. **算法与密钥匹配**：解析 JWT Header，确认 `alg` 为 `RS256`（严禁接受 `none` 或对称算法混淆攻击），并根据 `kid` 从 `/api/v1/oauth2/jwks` 中选取对应的 RSA 公钥验证数字签名。
2. **签发者校验（`iss`）**：验证 Payload 中的 `iss` 必须与 Discovery 文档返回的 `issuer` 完全一致（注意末尾不能有多余的 `/`）。
3. **受众校验（`aud`）**：验证 Payload 中的 `aud` 必须等于当前依赖方应用的 `client_id`，防止其他应用签发的令牌被跨应用混用（Token Substitution Attack）。
4. **时效性校验（`exp`）**：验证当前系统时间早于 `exp` 时间戳（允许配置合理的时钟偏移容忍度 Clock Skew，建议不超过 60 秒）。
5. **重放校验（`nonce`）**：若授权请求携带了 `nonce`，必须验证 `id_token` 中的 `nonce` 声明与当前用户会话中发起授权时存储的 `nonce` 完全相等。
6. **令牌类型校验（仅针对 `access_token`）**：若依赖方直接将 `access_token` 作为 API 凭证验签，必须确认 `token_type` 为 `"access"`，拒绝 `token_type` 为 `"refresh"` 的令牌访问业务接口。

### 6.4 用户身份标识绑定规范

- **必须以 `sub` 作为唯一外键**：在 `id_token`、`access_token` 与 `userinfo` 三个位置中，`sub` 始终返回同一用户 ID 字符串（例如 `"108"`）。依赖方应将 `(iss, sub)` 或 `sub` 作为本地用户表的唯一绑定标识。
- **禁止将 `preferred_username` 或 `name` 作为主键**：登录名、姓名、邮箱、部门属性可能随组织人事调整发生变更，仅可用于界面展示或冗余同步更新。

---

## 7. 代码集成示例

### 7.1 公开客户端：浏览器 SPA（TypeScript + PKCE S256）

适用于纯前端单页应用（`client_type = public`），通过 Web Crypto API 生成 `code_verifier` 与 `code_challenge`，不包含 `client_secret`：

```typescript
const OIDC_ISSUER = "https://sso.example.com/api/v1/oauth2";
const CLIENT_ID = "your_public_client_id";
const REDIRECT_URI = "https://spa.example.com/callback";

// Base64URL 编码（无 '=' 填充）
function base64UrlEncode(buffer: Uint8Array): string {
  const base64 = btoa(String.fromCharCode(...buffer));
  return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// 生成随机字符串
function generateRandomString(byteLength = 32): string {
  const bytes = new Uint8Array(byteLength);
  crypto.getRandomValues(bytes);
  return base64UrlEncode(bytes);
}

// 计算 S256 code_challenge
async function deriveCodeChallenge(codeVerifier: string): Promise<string> {
  const encoder = new TextEncoder();
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(codeVerifier));
  return base64UrlEncode(new Uint8Array(digest));
}

// 1. 发起授权跳转
export async function redirectToSsoAuthorize(): Promise<void> {
  const state = generateRandomString(16);
  const nonce = generateRandomString(16);
  const codeVerifier = generateRandomString(32);
  const codeChallenge = await deriveCodeChallenge(codeVerifier);

  sessionStorage.setItem("oauth_state", state);
  sessionStorage.setItem("oidc_nonce", nonce);
  sessionStorage.setItem("pkce_code_verifier", codeVerifier);

  const params = new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    scope: "openid profile email",
    state,
    nonce,
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
  });

  window.location.assign(`${OIDC_ISSUER}/authorize?${params.toString()}`);
}

// 2. 在回调路由 (/callback) 中用授权码换取令牌
export async function handleOAuthCallback(searchParams: URLSearchParams) {
  const code = searchParams.get("code");
  const returnedState = searchParams.get("state");
  const expectedState = sessionStorage.getItem("oauth_state");
  const codeVerifier = sessionStorage.getItem("pkce_code_verifier");

  // 立即清理一次性会话状态，防止重复提交
  sessionStorage.removeItem("oauth_state");
  sessionStorage.removeItem("pkce_code_verifier");

  if (!code || !returnedState || returnedState !== expectedState || !codeVerifier) {
    throw new Error("Invalid OAuth callback state or missing PKCE verifier");
  }

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CLIENT_ID,
    code,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier,
  });

  const response = await fetch(`${OIDC_ISSUER}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(`${err.error}: ${err.error_description}`);
  }

  return await response.json();
}
```

### 7.2 机密客户端：服务端 Web 应用（Python + Authlib）

适用于后端服务（`client_type = confidential`），使用 `server_metadata_url` 自动发现端点：

```python
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request

app = FastAPI()
oauth = OAuth()

oauth.register(
    name="y_sso",
    client_id="your_confidential_client_id",
    client_secret="your_confidential_client_secret",
    server_metadata_url="https://sso.example.com/api/v1/oauth2/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile email",
        "token_endpoint_auth_method": "client_secret_basic",
    },
)


@app.get("/login")
async def login(request: Request):
    redirect_uri = "https://app.example.com/oauth/callback"
    return await oauth.y_sso.authorize_redirect(request, redirect_uri)


@app.get("/oauth/callback")
async def auth_callback(request: Request):
    # 自动校验 state、调用 /token 换取令牌并校验 id_token
    token = await oauth.y_sso.authorize_access_token(request)
    # 调用 /userinfo 获取包含企业组织角色 (sso_roles) 的完整声明
    userinfo = await oauth.y_sso.userinfo(token=token)
    user_sub = userinfo["sub"]
    sso_roles = userinfo.get("sso_roles", [])
    return {"sub": user_sub, "sso_roles": sso_roles}
```

### 7.3 资源服务本地验签（Python + PyJWKClient）

适用于依赖方后端使用 JWKS 公钥在本地验证 `id_token` 或 `access_token`：

```python
import jwt
from jwt import PyJWKClient

OIDC_ISSUER = "https://sso.example.com/api/v1/oauth2"
JWKS_URI = f"{OIDC_ISSUER}/jwks"
CLIENT_ID = "your_client_id"

# PyJWKClient 内置公钥缓存（lifespan 单位：秒）
jwks_client = PyJWKClient(JWKS_URI, cache_jwk_set=True, lifespan=300)


def verify_sso_token(raw_token: str, expected_nonce: str | None = None) -> dict:
    signing_key = jwks_client.get_signing_key_from_jwt(raw_token)
    claims = jwt.decode(
        raw_token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=OIDC_ISSUER,
        audience=CLIENT_ID,
        leeway=60,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
    )
    if expected_nonce is not None and claims.get("nonce") != expected_nonce:
        raise jwt.InvalidTokenError("Nonce mismatch")
    return claims
```

---

## 8. 错误码与故障排查

所有 OAuth 2.0 / OIDC 端点在发生错误时均返回标准 JSON 结构：

```json
{
  "error": "invalid_grant",
  "error_description": "授权码已过期"
}
```

### 标准错误码字典

以下错误说明严格按照「错误现象 → 触发原因 → 处理措施」列出：

| HTTP 状态码 | `error` 错误码 | 典型 `error_description` | 错误现象、触发原因与处理措施 |
| :---: | :--- | :--- | :--- |
| `400` | `invalid_request` | `仅支持 response_type=code` | **现象**：授权请求被拒绝。<br>**原因**：`response_type` 参数缺失或传入了非 `code` 的值（如 `token`）。<br>**措施**：将 `/authorize` 请求中的 `response_type` 固定设置为 `code`。 |
| `400` | `invalid_request` | `客户端不存在: <client_id>` / `应用已禁用: <name>` | **现象**：授权请求被拒绝。<br>**原因**：传入的 `client_id` 未在 SSO 注册，或该应用已被管理员停用。<br>**措施**：核对客户端配置中的 `client_id`，并联系 SSO 管理员确认应用处于启用状态。 |
| `400` | `invalid_request` | `重定向URI无效: <uri>` | **现象**：授权请求被拒绝。<br>**原因**：请求中的 `redirect_uri` 与应用后台登记的 `redirect_uris` 不一致（协议、域名、端口或尾部斜杠存在差异）。<br>**措施**：将请求中的 `redirect_uri` 修改为与应用管理台完全一致的 URI。 |
| `400` | `invalid_request` | `公开客户端必须提供 code_challenge` / `公开客户端仅支持 code_challenge_method=S256` | **现象**：公开客户端授权请求被拒绝。<br>**原因**：应用类型为 `public`，但未传 `code_challenge` 或算法不是 `S256`。<br>**措施**：在客户端启用 PKCE 扩展，传入 `code_challenge` 并设置 `code_challenge_method=S256`。 |
| `400` | `invalid_request` | `authorization_code 需要 code 和 redirect_uri 参数` | **现象**：令牌交换请求失败。<br>**原因**：调用 `/token` 时缺少必填的表单字段 `code` 或 `redirect_uri`。<br>**措施**：使用 `application/x-www-form-urlencoded` 格式完整提交 `grant_type`、`code` 和 `redirect_uri`。 |
| `401` | `invalid_client` | `缺少客户端ID` / `缺少客户端凭证` / `客户端密钥错误` | **现象**：令牌端点客户端身份认证失败。<br>**原因**：未传递 `client_id`，或 `confidential` 客户端未传/传错了 `client_secret`。<br>**措施**：核对 `client_id` 与 `client_secret`；若使用 HTTP Basic 认证，确保按 `client_id:client_secret` 格式进行 Base64 编码。 |
| `401` | `invalid_client` | `来源IP不在应用白名单内` | **现象**：调用 `/token` 被拒绝。<br>**原因**：依赖方后端服务器的出口 IP 不在应用配置的 `allowed_ip_cidrs` 白名单内，或反向代理未配置入 `ip_access.trusted_proxies`。<br>**措施**：将依赖方服务器出口 IP 加入该应用的 IP 白名单；若经过网关转发，确认网关 IP 已加入 SSO 的 `trusted_proxies`。 |
| `400` | `invalid_grant` | `授权码无效` / `授权码已被使用` / `授权码已过期` | **现象**：授权码换取令牌失败。<br>**原因**：`code` 不存在、超过 5 分钟有效期、或被重复提交（如前端页面刷新、双次触发回调请求）。<br>**措施**：确保回调页面每个 `code` 仅发起一次 `/token` 请求；若已失效，重新引导用户发起 `/authorize` 授权流程。 |
| `400` | `invalid_grant` | `授权码与客户端不匹配` / `redirect_uri 不匹配` | **现象**：授权码换取令牌失败。<br>**原因**：调用 `/token` 的 `client_id` 或 `redirect_uri` 与生成该 `code` 时传入的参数不一致。<br>**措施**：确保 `/token` 与 `/authorize` 阶段使用完全相同的 `client_id` 和 `redirect_uri`。 |
| `400` | `invalid_grant` | `缺少 code_verifier` / `code_verifier 验证失败` | **现象**：PKCE 校验失败。<br>**原因**：未传 `code_verifier`，或 `code_verifier` 经 SHA-256 + Base64URL 计算后的结果与授权阶段的 `code_challenge` 不一致。<br>**措施**：检查授权前在 `sessionStorage` 中保存的 `code_verifier` 是否在回调阶段被正确读取并原样提交，确保 Base64URL 编码未包含末尾 `=` 填充符。 |
| `400` | `invalid_grant` | `refresh_token 无效或已过期` / `用户不存在或已禁用` | **现象**：刷新令牌失败。<br>**原因**：`refresh_token` 已超过有效期、签名不合法、或对应用户账号已被禁用。<br>**措施**：清理依赖方本地会话，重新将用户重定向至 `/authorize` 进行登录。 |
| `400` | `unsupported_grant_type` | `不支持的授权类型: <grant_type>` | **现象**：令牌请求被拒绝。<br>**原因**：`grant_type` 传入了不支持的值（如 `client_credentials` 或 `password`）。<br>**措施**：将 `grant_type` 设置为 `authorization_code` 或 `refresh_token`。 |
| `401` | `invalid_token` | `缺少或无效的 Bearer Token` / `access_token 无效或已过期` | **现象**：调用 `/userinfo` 返回 `401`（附带 `WWW-Authenticate: Bearer` 响应头）。<br>**原因**：未携带 `Authorization: Bearer <access_token>` 请求头，或 `access_token` 已过期、签名不匹配、错传了 `refresh_token`。<br>**措施**：检查请求头格式（`Bearer` 后有一个空格）；若令牌已过期，先调用 `/token` 刷新令牌后再重试。 |
| `403` | `access_denied` | `来源IP不在应用白名单内` | **现象**：调用 `/userinfo` 返回 `403`。<br>**原因**：发起 `/userinfo` 请求的客户端 IP 不在应用配置的 `allowed_ip_cidrs` 白名单内。<br>**措施**：在 SSO 管理后台将该应用后端服务器 IP 添加至 IP 白名单。 |

---

## 9. 安全基线与上线检查清单

第三方应用在正式上线生产环境前，必须逐项核对以下安全基线要求：

- [ ] **全链路 TLS/HTTPS**：生产环境下 SSO 的 `issuer`、各协议端点以及依赖方的所有 `redirect_uri` 均已启用 HTTPS，禁止明文 HTTP 传输授权码与令牌。
- [ ] **客户端类型与密钥隔离**：浏览器 SPA、移动端与桌面端应用已配置为 `public` 客户端并启用 `PKCE (S256)`，前端代码、构建产物及环境变量中不存在任何 `client_secret`。
- [ ] **CSRF 防护（`state`）**：依赖方在每次发起 `/authorize` 请求前均生成高熵随机 `state` 并绑定至当前浏览器会话，在回调处理时严格比对 `state` 参数，不匹配时立即中止流程。
- [ ] **重放攻击防护（`nonce`）**：依赖方在 OIDC 授权请求中生成并传入随机 `nonce`，并在换取 `id_token` 后校验 Payload 中的 `nonce` 声明与会话记录一致。
- [ ] **授权码单次消费控制**：依赖方回调路由已做防抖或状态锁控制，确保同一个 `code` 不会被并发或重复提交至 `/token` 端点。
- [ ] **JWT 完整验签**：若采用本地 JWKS 验签，已同时校验签名算法（`RS256`）、签发者（`iss`）、受众（`aud` 等于本应用 `client_id`）及过期时间（`exp`）。
- [ ] **唯一身份标识绑定**：依赖方数据库使用 `sub` 作为用户唯一关联标识，未将可能发生变更的 `preferred_username`、`name` 或 `email` 作为持久化主键。
- [ ] **后端通道 IP 白名单（机密客户端）**：机密客户端已在 SSO 应用配置中登记后端服务器出口 IP / CIDR，限制非授权网络节点调用 `/token` 与 `/userinfo`。
