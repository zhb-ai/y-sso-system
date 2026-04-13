# SSO 对接问题真实性评估与整改落地方案

> 产出目的：基于 `docs/analysis-discovery-and-sub-consistency.md` 与 `docs/sso-integration-requirements(2).md`，结合当前代码实现，判断哪些问题真实存在、哪些属于增强项、哪些当前无需修改，并给出可执行的整改方案。
>
> 说明：本文档只做分析和落地方案设计，不包含实际代码改动。
>
> 分析日期：2026-04-13

---

## 一、结论先看

### 1.1 分类结论

| 编号 | 议题 | 真实性判断 | 当前对接是否必须修改 | 结论 |
|---|---|---|---|---|
| 1 | 缺少标准 OIDC Discovery 端点 | **部分成立** | **否** | 当前系统确实没有 `/.well-known/openid-configuration`，但并非“完全没有发现能力”，因为已有 RFC 8414 元数据端点 |
| 2 | `sub` 在 JWT 和 UserInfo 之间不一致 | **成立** | **是** | 这是当前实现中的真实 Bug，且会直接影响下游身份一致性 |
| 3 | JWKS 公钥端点缺失 | **成立** | **否** | 这是“标准 OIDC/JWT 本地验签能力缺失”，不是当前手动对接模式的阻塞项 |
| 4 | issuer 使用 localhost 而非外部地址 | **部分成立** | **否** | 元数据端点的 issuer 来源问题已确认存在；JWT 中 `iss` 是否已错，当前仓库无法直接证实，需要运行时确认 |
| 5 | 不支持 PKCE / 无公开客户端支持 | **成立** | **否（测试可不改）/ 是（浏览器生产接入建议改）** | 对浏览器 SPA 来说这是明确的安全能力缺口，但不阻塞当前用 `client_secret` 跑通联调 |
| 6 | UserInfo 响应 email 为 null | **现象成立，根因不是代码 Bug** | **否** | 更像数据治理问题，不建议优先走代码改造 |
| 7 | 管理后台缺少第三方对接配置面板 | **成立** | **否** | 这是产品易用性缺口，不是协议正确性问题 |

### 1.2 推荐优先级

| 优先级 | 事项 |
|---|---|
| P0 | 修复 `sub` 一致性问题 |
| P1 | 明确当前对接采用“手动端点 + UserInfo 校验”模式，并形成标准接入说明 |
| P2 | 增加 OIDC Discovery 端点，并修正元数据中的 issuer 来源 |
| P3 | 增加 PKCE / Public Client 支持 |
| P4 | 迁移到 RS256 并提供 JWKS |
| P4 | 增加管理后台“第三方对接配置”面板 |
| 运维治理 | 补齐用户 email 数据，不作为代码整改主线 |

### 1.2.1 整改执行清单

- [x] 修复 `sub` 一致性，统一为 `str(user.id)`
- [x] 新增标准 OIDC Discovery 端点 `/.well-known/openid-configuration`
- [x] 修正 OAuth2 元数据中的 `issuer` / 端点基础地址来源
- [ ] 增加 PKCE / Public Client 支持
- [ ] 迁移到 RS256 并提供 JWKS
- [x] 增加管理后台“第三方系统对接配置”面板
- [ ] 补齐用户 email 数据治理流程

### 1.3 当前最短可落地路线

如果目标是“先让 Data Formulator 尽快接上 SSO”，当前**不需要等所有问题都修完**。最短路径是：

1. 继续使用现有 `authorize`、`token`、`userinfo` 三个端点。
2. 采用手动端点配置，不依赖 Discovery。
3. 继续使用 UserInfo 回查验证 token，不依赖 JWKS。
4. 先修复 `sub` 一致性；如果短期来不及修，可临时在对接方继续使用 `preferred_username` 作为身份字段兜底，但该做法只作为过渡，不作为长期身份主键。

换句话说：**当前必须修的是 `sub` 一致性；Discovery、JWKS、PKCE、对接面板都可以分阶段做。**

---

## 二、评估依据

本次结论来自以下事实核验，而不是只根据对接文档推断：

- `app/api/v1/oauth2.py`
- `app/domain/application/services.py`
- `app/domain/application/entities.py`
- `app/api/v1/application.py`
- `frontend/src/pages/applications/Index.vue`
- `app/config.py`
- `config/settings.yaml_demo`
- `app/api/routes.py`

同时有两个边界要说明：

1. 当前仓库只能确认本项目代码中的行为，无法直接看到 `yweb` 依赖内部 `JWTManager` 的完整实现。
2. 因此，关于 JWT 最终是否一定带有 `iss`、`aud` 以及 `RS256` 是否可直接启用，**需要在实施前做一次运行时验证或查看 `yweb` 源码**。

---

## 三、问题逐项判断

## 3.1 问题 1：缺少标准 OIDC Discovery 端点

### 判断

这是一个**表述需要修正的真实问题**。

真实情况不是“系统没有发现端点”，而是：

- 已有 `GET /api/v1/oauth2/.well-known/oauth-authorization-server`
- 缺少标准 OIDC 客户端更常用的 `GET /.well-known/openid-configuration`
- 当前已有端点位于 `/api/v1/oauth2` 路径下，且返回的是 OAuth2 元数据，不是完整 OIDC Discovery 文档

### 是否建议修改

建议修改，但**不是当前 Data Formulator 接入的前置条件**。

### 为什么当前不是必须改

对接需求文档已经明确给出“模式 B：手动端点”，而当前系统已经具备：

- `authorize`
- `token`
- `userinfo`

因此当前可以接，不需要等 Discovery。

### 修改影响范围

影响范围较小，主要是：

- 后端新增一个根路径路由
- 元数据返回内容补全
- 对已有集成几乎没有破坏性，因为这是新增能力

涉及模块：

- `app/main.py` 或单独新增根级元数据路由
- `app/api/v1/oauth2.py`
- 接入文档

### 落地方案

建议采用“增量兼容”方案：

1. 保留现有 RFC 8414 端点，不做下线。
2. 新增根路径 `/.well-known/openid-configuration`。
3. Discovery 中的端点地址统一引用外部可访问地址。
4. Discovery 中只声明当前真实支持的能力，不要提前声明未实现的 JWKS 或 PKCE。

### 实施结果预期

实施后会带来两类收益：

- 标准 OIDC 客户端可自动发现端点
- 对接文档从“手工抄 6-7 个地址”缩减为“给一个 issuer 即可”

---

## 3.2 问题 2：`sub` 在 JWT 和 UserInfo 之间不一致

### 判断

这是**确认存在的真实 Bug**，而且是本轮最应该优先修的点。

当前代码中：

- `exchange_code_for_token()` 里 `sub=user.username`
- `get_userinfo()` 里 `sub=str(user.id)`

这意味着同一个用户在两个协议面上暴露成了两个不同身份。

### 为什么这是必须修改

它会直接影响下游系统如何识别“同一个人”：

- 使用 JWT 解析时，用户标识是用户名
- 使用 UserInfo 时，用户标识是数据库 ID
- 同一用户在不同校验方式下会被视为不同主体

这不是“规范洁癖”，而是**身份主键不一致**。

### 修改影响范围

这是一个改动点很小、业务影响却很大的问题。

影响范围包括：

- `app/domain/application/services.py`
- 所有依赖 `sub` 建立用户目录、缓存键、租户隔离键、工作空间路径的下游系统
- 现有已签发 token 在过期前仍会保留旧 `sub`

外部系统影响重点：

- Data Formulator
- 任何以后要做本地 JWT 验签的系统
- 任何把 `sub` 当作唯一用户键落库的系统

### 推荐修复方向

推荐把 `sub` 统一为 `str(user.id)`，原因如下：

- `user.id` 相对稳定
- 当前 UserInfo 已经是这个口径
- 不需要数据库迁移
- 比统一成 `username` 更符合“唯一且不易变化”的身份主键原则

### 不建议的做法

不建议继续把 `preferred_username` 当长期主键使用，因为：

- 它更适合展示和兼容
- 不保证不可变
- 不能替代 `sub`

### 可执行落地步骤

1. 先确认现有下游系统是否把 `sub` 持久化为业务主键。
2. 修改 token 生成逻辑，使 JWT 中 `sub` 与 UserInfo 保持一致。
3. 给所有已对接系统发变更通知，说明 `sub` 将统一为用户 ID。
4. 对仍依赖用户名工作空间的系统，设置过渡窗口，先继续使用 `preferred_username` 兜底。
5. 在过渡窗口结束后，让下游系统回归使用标准 `sub`。

### 回滚和过渡建议

这个问题最大的风险不是代码本身，而是下游数据映射。

建议按下面方式推进：

1. 先在测试环境验证新 token 的 `sub` 是否与 UserInfo 完全一致。
2. 统计下游是否存在以旧 `sub=username` 存储的数据。
3. 如存在历史数据，先做映射表或迁移脚本，再切生产。
4. 切换当天控制 token 过期窗口，避免新旧 `sub` 长时间并存。

---

## 3.3 问题 3：JWKS 公钥端点缺失

### 判断

这是**真实存在的能力缺口**，但它不是“当前必须马上修”的问题。

当前仓库已能确认两件事：

1. 没有任何 JWKS 端点实现。
2. 默认 JWT 算法是 `HS256`。

### 关键判断

这里最重要的一点是：

**不能为了“看起来像标准”而先做一个假的 JWKS 端点。**

如果仍然使用 `HS256`：

- 签名密钥是对称密钥
- 公钥无法安全公开给第三方
- 所谓 JWKS 端点没有真实价值

所以原分析文档里“先补一个 JWKS 端点占位”的想法，不建议采纳。

### 是否建议修改

建议改，但应放到**中期架构升级**中处理，而不是当前联调阶段。

### 修改影响范围

这个问题一旦真正改，会波及面比较大：

- JWT 签发与验签链路
- `yweb` 的 JWTManager 能力边界
- 配置文件
- 可能的密钥管理方式
- 对接方验签方式

涉及模块通常包括：

- `settings.yaml`
- `app/api/v1/oauth2.py`
- 与 JWT 创建/校验相关的服务层
- 部署环境中的密钥文件或密钥托管系统

### 推荐落地方案

建议拆成两个阶段：

#### 阶段 A：当前阶段不做 JWKS，继续 UserInfo 校验

适用场景：

- 当前只是尽快接通 Data Formulator
- 对性能要求还不高
- 不希望扩大改造范围

做法：

1. 明确对接方当前采用 UserInfo 回查验 token。
2. 不声明 JWKS，不在 Discovery 中写入虚假的 `jwks_uri`。

#### 阶段 B：中期迁移到 RS256 + JWKS

做法：

1. 先确认 `yweb>=0.1.2` 对 RS256 的支持情况。
2. 如支持，生成 RSA 密钥对并纳入配置管理。
3. 把 access token 签名算法切到 `RS256`。
4. 新增 `GET /api/v1/oauth2/jwks`。
5. 在 Discovery 中声明真实 `jwks_uri`。
6. 让对接方从“UserInfo 回查”逐步切到“本地验签”。

### 风险提示

这一项不建议和 `sub` 修复同一批次上线。原因是：

- `sub` 是协议主键问题
- JWKS/RS256 是签名体系变更

两者叠加会让排障复杂度明显上升。

---

## 3.4 问题 4：issuer 使用 localhost 而非外部地址

### 判断

这是一个**需要拆开判断的部分成立问题**。

#### 已确认成立的部分

当前 OAuth2 元数据端点中的 `issuer` 来源是 `request.base_url`，这在反向代理场景下确实可能不稳定，也不适合作为长期对外协议地址。

这部分问题已经被代码直接证实。

#### 不能直接下结论的部分

“当前 JWT 的 `iss` claim 一定是 localhost”这件事，**当前仓库无法直接证明**。

原因是：

- JWT 是通过 `yweb` 的 `JWTManager` 生成
- 当前项目代码里没有直接写出 `iss` 的构造逻辑
- 需要抓取实际 token 或查看 `yweb` 源码才能确认

所以更准确的说法应该是：

**元数据 issuer 来源有问题已确认；JWT `iss` 是否同样错误，需要补一次运行时核验。**

### 是否建议修改

建议修改，但对当前“手动端点 + UserInfo 校验”模式不是前置阻塞。

### 什么时候它会变成必须改

以下场景就必须改：

1. 要支持标准 OIDC Discovery。
2. 要支持 JWKS 本地验签。
3. 对接方会严格校验 `issuer`。

### 修改影响范围

影响范围中等，主要是：

- 配置文件中的外部基地址
- 元数据端点输出
- 未来若 JWT 也要显式带 `iss`，则要影响 token 生成链路

涉及模块：

- `app/config.py`
- `config/settings.yaml`
- `app/api/v1/oauth2.py`
- 可能还包括 `yweb` JWT 配置层

### 推荐落地方案

建议按“两步确认、一步整改”执行：

1. 先抓取线上或测试环境实际签发的 access token，解码确认是否存在 `iss`，值是什么。
2. 把元数据端点中的 `issuer` 和端点拼接基础地址改为显式配置项。
3. 把部署环境 `base_url` 配成真实外部访问地址，并核对网关、反向代理、TLS 终止点对外暴露的最终 URL 是否一致。

### 当前阶段建议

对于当前 Data Formulator 手动端点模式：

- 可以先不把它作为阻塞项
- 但应在第二阶段和 Discovery 一起修正

---

## 3.5 问题 5：不支持 PKCE / 无公开客户端支持

### 判断

这是**真实存在的安全能力缺口**。

当前代码已能明确确认：

- `token` 端点强制要求 `client_secret`
- 授权码实体没有 `code_challenge`、`code_challenge_method`
- 当前没有任何 PKCE 相关参数处理
- `Application.client_secret` 为必填

### 是否必须修改

要分场景看：

- 如果只是尽快联调、且暂时接受机密客户端模式，可以先不改
- 如果要让浏览器 SPA 以更合理的生产方式接入，建议尽快改

所以它不是“当前能不能接”的硬阻塞，但它是“能不能安全长期用”的重要问题。

如果对接形态满足以下条件中的任意一项，应把 PKCE 从“推荐修改”上调为“准必须项”：

- 客户端是浏览器 SPA
- `client_secret` 已经下发到前端代码或浏览器环境
- 计划用于正式生产环境，而不只是短期内网联调

### 修改影响范围

这一项是明确的跨层改造，至少涉及：

- 数据模型
- 授权端点
- token 端点
- 应用管理后台
- 对接文档

涉及模块：

- `app/domain/application/entities.py`
- `app/domain/application/services.py`
- `app/api/v1/oauth2.py`
- `app/api/v1/application.py`
- `frontend/src/pages/applications/Index.vue`

### 推荐落地方案

建议用“兼容式增强”而不是“替换式改造”：

1. 保留现有机密客户端模式，保证已有系统不受影响。
2. 新增 Public Client 类型。
3. 当应用类型是 Public Client 时，要求 PKCE，且不要求 `client_secret`。
4. 当应用类型是 Confidential Client 时，继续沿用现有 `client_secret` 逻辑。

### 分阶段实施建议

第一步：

- 给应用模型增加客户端类型字段
- 后台允许创建 Public Client

第二步：

- `authorize` 接受 `code_challenge` 和 `code_challenge_method`
- 授权码记录保存 PKCE 参数

第三步：

- `token` 在 Public Client 场景下改为校验 `code_verifier`
- Confidential Client 继续走旧逻辑

### 验收标准

改完后应该同时满足：

1. 原有机密客户端不受影响。
2. 浏览器 SPA 可不携带 `client_secret` 完成授权码交换。
3. Discovery 中只在真正支持时才声明 `code_challenge_methods_supported=["S256"]`。

---

## 3.6 问题 6：UserInfo 响应 email 为 null

### 判断

这是**真实现象**，但优先应当按**数据问题**处理，而不是代码问题。

从当前实现看，UserInfo 已在读用户的 `email` 字段，没有明显逻辑错误。

### 是否建议修改

当前不建议以“改代码”为主线处理。

### 为什么不用优先改代码

如果源数据本来就没有 email：

- 改 UserInfo 接口也变不出来真实邮箱
- 贸然从别的字段拼装 email，反而会制造脏数据

### 推荐处理方式

建议按运维治理方式落地：

1. 盘点哪些用户 `email` 为空。
2. 确认邮箱的权威来源是哪个系统。
3. 补同步链路，而不是在 UserInfo 临时兜底造值。
4. 如果某些下游系统确实强依赖 email，再评估是否增加“明确来源的 fallback”。

### 影响范围

主要影响：

- 用户展示信息完整性
- 某些把 email 当登录展示名的下游系统

不直接影响：

- 授权码流程
- token 交换
- UserInfo 基本可用性

---

## 3.7 问题 7：管理后台缺少第三方对接配置面板

### 判断

这是**真实存在的产品能力缺口**。

当前前端应用管理页只能看到：

- 应用列表
- `client_id`
- 重置后的 `client_secret`

不能直接看到：

- issuer
- Discovery URL
- authorize URL
- token URL
- userinfo URL
- 是否支持 PKCE
- token 签名算法

### 是否必须修改

不是协议必须项，但非常建议做。

### 修改影响范围

影响范围中等，主要是前后端联动：

- 前端增加“对接配置”展示入口
- 后端提供统一的端点配置数据

涉及模块：

- `frontend/src/pages/applications/Index.vue`
- `app/api/v1/application.py` 或 `app/api/v1/config.py`
- `app/config.py`

### 推荐落地方案

建议分为“快速版”和“标准版”。

#### 快速版

只解决“让实施同学少沟通、少抄地址”：

1. 后端返回 `base_url`、支持能力、常用端点模板。
2. 前端在应用详情或密钥弹窗中增加“第三方对接配置”区域。
3. 提供“复制单项”和“复制全部”。

#### 标准版

在快速版基础上进一步增强：

1. 同时展示当前应用类型是 Public 还是 Confidential。
2. 展示当前系统是否已支持 Discovery、PKCE、JWKS。
3. 展示推荐给第三方系统的配置示例。

### 适合放在哪个阶段

建议放到协议正确性问题稳定之后再做，也就是：

- 在 `sub` 修复完成后
- 最好和 Discovery 一起上线

这样面板展示的信息才不会频繁变化。

---

## 四、哪些要改，哪些当前不用改

## 4.1 必须修改

| 事项 | 原因 |
|---|---|
| `sub` 一致性 | 已是当前真实 Bug，且会影响下游身份主键 |

## 4.2 建议修改，但可分阶段做

| 事项 | 当前是否阻塞接入 | 建议时机 |
|---|---|---|
| 根路径 OIDC Discovery | 否 | 第二阶段 |
| 元数据 issuer 改为显式配置 | 否 | 第二阶段 |
| PKCE / Public Client | 联调不阻塞，生产建议尽快补齐 | 第三阶段 |
| 管理后台对接配置面板 | 否 | 第二或第四阶段 |

## 4.3 属于中期架构升级，不建议现在硬上

| 事项 | 原因 |
|---|---|
| RS256 + JWKS | 影响签名体系、配置、部署和下游验签策略，不适合和当前联调耦合推进 |

## 4.4 当前不建议走代码改造

| 事项 | 原因 |
|---|---|
| email 为 null | 更像主数据质量问题，应先补源数据和同步链路 |

---

## 五、建议的实施路线图

## 5.0 开工前门禁检查

在真正进入阶段 1 之前，建议先完成以下门禁确认：

1. 确认 Data Formulator 以及其他已接系统，当前到底使用 `sub`、`preferred_username`，还是其他字段作为用户主键。
2. 确认下游是否把用户主键写入数据库、目录路径、缓存键或工作空间标识。
3. 确认生产和联调环境的外部访问地址、网关路径、TLS 终止点与 `base_url` 配置一致。
4. 确认当前生产实际安装的 `yweb` 版本，以及该版本对 `iss`、`aud`、RS256 的支持情况。
5. 确认 Discovery 根路径在网关或反向代理层面是否允许直接暴露。

## 5.1 第一阶段：先把当前接入跑稳

目标：**不扩大改造范围，先让 Data Formulator 稳定接入。**

执行项：

1. 明确当前采用手动端点模式。
2. 继续使用 UserInfo 校验 token。
3. 修复 `sub` 一致性。
4. 如下游已有用户名路径依赖，短期继续允许其使用 `preferred_username` 兜底。
5. 在实施前明确下游系统的用户主键迁移方案，避免 `sub` 修复后出现历史数据无法关联。

交付物：

- 一份对接说明
- 一份 `sub` 切换通知
- 一次联调验收记录

验收标准：

1. 登录流程可用。
2. UserInfo 返回稳定。
3. 新签发 token 的 `sub` 与 UserInfo 完全一致。

## 5.2 第二阶段：补协议正确性和可发现性

目标：**让系统对标准 OIDC 客户端更友好。**

执行项：

1. 新增 `/.well-known/openid-configuration`。
2. 修正元数据中的 issuer 来源为显式配置。
3. 统一梳理 `base_url` 的配置方式。
4. 不要提前声明尚未支持的 `jwks_uri` 和 PKCE 能力。
5. 在网关、反向代理、Ingress 层确认根路径 `/.well-known/openid-configuration` 能实际转发到本应用，而不是只在应用内可用。

验收标准：

1. 根路径 Discovery 可访问。
2. 返回内容与实际支持能力一致。
3. 对外地址与部署地址一致。

## 5.3 第三阶段：补浏览器客户端安全能力

目标：**让浏览器 SPA 可以不用暴露 `client_secret`。**

执行项：

1. 增加 Public Client 类型。
2. 增加 PKCE 支持。
3. 保持 Confidential Client 向后兼容。

验收标准：

1. Public Client 可走 PKCE。
2. Confidential Client 旧流程不受影响。
3. 文档和后台展示同步更新。

## 5.4 第四阶段：做标准化 JWT 验签能力

目标：**支持下游本地验签，降低对 UserInfo 回查依赖。**

执行项：

1. 确认 `yweb` 是否支持 RS256。
2. 迁移签名算法。
3. 提供 JWKS 端点。
4. 让对接方逐步从 UserInfo 校验切到本地验签。

验收标准：

1. JWKS 可访问。
2. 下游可使用公钥完成本地验签。
3. token 的 `iss`、`sub`、`aud` 与 Discovery 保持一致。

## 5.5 第五阶段：提升实施体验

目标：**让第三方对接不再依赖口头沟通。**

执行项：

1. 后台增加“第三方对接配置”面板。
2. 支持复制全部配置。
3. 展示当前支持能力和推荐接入方式。

验收标准：

1. 实施同学不查代码也能拿到全部接入参数。
2. 新接入应用可按后台配置直接联通。

---

## 六、建议的最终决策

如果站在“现在就要可落地”的角度，建议做下面这个决策组合：

### 决策 A：当前接入策略

- 先按手动端点模式接入 Data Formulator
- 暂不把 Discovery、JWKS、PKCE 作为上线阻塞项

### 决策 B：当前必须修复项

- 立即修复 `sub` 一致性

### 决策 C：下一批要做的标准化改造

- OIDC Discovery
- issuer 配置规范化

### 决策 D：中期能力升级

- PKCE / Public Client
- RS256 + JWKS

### 决策 E：不纳入本轮代码整改的事项

- email 为 null，先按数据治理处理

---

## 七、实施前必须补的两个确认动作

在真正开始改代码前，建议先补两个确认动作，否则第 2、4、5 阶段容易误判：

1. 抓取当前实际签发的 access token，确认是否存在 `iss`、`aud`，值分别是什么。
2. 确认 `yweb>=0.1.2` 的 `JWTManager` 是否支持 RS256，以及支持方式是什么。

如果这两个动作没做，后续关于 issuer 和 JWKS 的设计很容易建立在错误前提上。

---

## 八、一句话总结

这批问题里，**真正必须立即修的是 `sub` 不一致**；**Discovery、issuer、PKCE、JWKS 都是明确存在但可分阶段推进的能力建设**；**email 为 null 不应当优先用代码修，而应当先做数据治理**。
