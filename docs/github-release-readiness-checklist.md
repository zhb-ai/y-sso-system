# GitHub 发布前整改清单

## 目的

这份清单用于指导 `y-sso-system` 在公开发布到 GitHub 前完成必要整改，目标不是“内部可用”，而是：

- 外部开发者可以理解项目定位
- 外部开发者可以按文档完成最小启动
- 外部系统可以按文档完成基础 OIDC 对接
- 仓库具备基本的开源发布要素

## 当前状态摘要

当前项目已经具备基础可用的 SSO / OAuth2 / OIDC 主链路，且近期已完成这些修正：

- 已重写 `README.md`，修正了大部分接口路径、配置说明和启动步骤
- 已将 OIDC `issuer` 从 `base_url` 中解耦，新增 `oidc_issuer`
- 已只保留 `/api/v1/oauth2/.well-known/openid-configuration`
- 已补充 `jwt_key_id` 与旧版 `yweb` 兼容说明

但如果目标是“公开到 GitHub 后，别人 clone 下来就能按文档跑起来并对接”，当前仍有明显缺口。

## 优先级定义

- `P0`：公开发布前必须完成，否则外部用户高概率第一天就卡住
- `P1`：建议在首个公开版本完成，否则会影响专业度、集成成功率或维护成本
- `P2`：增强项，不阻塞首次公开发布，但会影响长期可用性

## P0：发布前必须完成

- [ ] 补充正式 `LICENSE` 文件
  - 当前决定为“暂不加 LICENSE，先保留为未授权状态”
  - 这不影响私有使用，但若要以开源方式公开发布到 GitHub，仍然是阻塞项
  - 届时需要新增根目录 `LICENSE`，并在 `README.md` 中声明许可证类型

- [x] 明确 `yweb` 的获取方式
  - 已将 `requirements.txt` 改为公开 GitHub 源安装，并固定到 `0.1.3`：`yweb @ git+https://github.com/yafo-ai/yweb-core.git@0.1.3`
  - `README.md` 也已同步补充单独安装说明，避免对外使用时依赖隐含私有源

- [x] 统一开发环境端口
  - `frontend/vite.config.js`、`dev_server.py`、`app/config.py`、`config/settings.yaml_demo` 已统一到 `8000`
  - `README.md`、`README_DEV.md`、`CONFIG_GUIDE.md` 与集成文档中的默认口径也已同步

- [x] 修正 `README_DEV.md` 的过期端口说明
  - `README_DEV.md` 中 `--port` 默认值、访问地址、注意事项已与 `dev_server.py` 保持一致

- [x] 校准 `CONFIG_GUIDE.md` 中仍可能沿用旧端口/旧示例的内容
  - `CONFIG_GUIDE.md` 已同步到 `8000` 口径
  - 基础 URL、OIDC issuer 与示例命令已统一

- [x] 确认并公开真实仓库地址
  - `README.md` 已替换为真实 GitHub 地址：`https://github.com/zhb-ai/y-sso-system.git`

- [x] 决定是否提供“开箱即用开发密钥生成脚本”
  - 当前决定为：不额外提供脚本，保留 `README.md` 中的 OpenSSL 命令方案
  - 对首次安装而言，这已经足够明确，后续如需降低门槛再单独补脚本

- [x] 梳理“首次安装”唯一推荐流程
  - 已确认官方推荐流程为 `alembic upgrade head` + `python init_db.py`
  - `README.md`、`README_DEV.md`、`README_ADMIN.md` 已统一到该口径
  - `docs/version-upgrade-and-integration-guide.md` 也已明确其适用范围为升级场景，避免与首次安装混淆

## P1：首个公开版本建议完成

- [ ] 增加 `.github/workflows` 基础 CI
  - 至少包含：安装依赖、运行关键测试、可选的 lint
  - 这样外部贡献者和使用者能看到仓库的基本健康状态

- [ ] 提供最小部署方案
  - 当前仓库缺少 `Dockerfile` / `docker-compose` / 部署示例
  - 至少应提供一种官方推荐部署方式

- [ ] 拆分公开文档与内部过程文档
  - 当前 `docs/` 中混有 `plans`、`specs`、历史分析文档
  - 建议增加 `docs/README.md` 作为索引，或把内部过程文档移到单独目录

- [ ] 增加“外部接入入口文档”
  - 推荐保留以下文档作为公开入口：
  - `README.md`
  - `docs/version-upgrade-and-integration-guide.md`
  - `docs/df-superset-developer-integration-guide.md`
  - 其他偏内部文档建议标记为历史/设计资料

- [ ] 增加真实集成测试
  - 当前 OAuth/OIDC 相关测试已覆盖核心服务逻辑，但 API 层仍偏 stub
  - 建议增加“真实路由 + 配置 + 测试数据库”的端到端测试

- [ ] 补充标准化 OIDC 元数据声明
  - 建议评估是否在 discovery 中声明公开客户端常见的 `token_endpoint_auth_methods_supported: ["none"]`
  - 以避免部分客户端误判能力

- [ ] 评估 `confidential client` 是否默认也要求 PKCE
  - 当前 `public` 客户端强制 `PKCE(S256)`
  - 若面向更标准化的 OAuth 2.1 生态，建议评估对 `confidential` 的默认策略

- [ ] 明确 `userinfo` 的 claims 策略
  - 当前 `userinfo` 返回了系统自定义字段，例如 `roles`、`sso_roles`、`user_code`
  - 建议明确说明哪些属于标准字段，哪些属于扩展字段

- [ ] 评估授权确认页的 consent 行为
  - 当前 `GET /authorize` 在用户已登录时会直接发码
  - 如果项目面向更广泛外部接入，建议评估是否引入显式 consent 策略

## P2：增强项

- [ ] 增加标准协议外围能力
  - Token revocation
  - Introspection
  - Logout / session management

- [ ] 增加示例客户端
  - 最好提供最小 Web 应用或脚本示例
  - 让第三方更容易验证授权码流程

- [ ] 增加发布级别的截图或演示说明
  - 例如管理后台、应用接入配置面板、SSO 授权页

- [ ] 输出对外 Roadmap
  - 说明当前版本已具备什么
  - 下一阶段准备补什么

- [ ] 增加安全章节
  - 建议单独补充“生产部署安全建议”
  - 包括 HTTPS、密钥轮换、可信代理、IP 白名单、数据库选型等

- [ ] 增加版本兼容矩阵
  - 包括 `yweb` 版本、Python 版本、前端 Node 版本、是否支持 `key_id` 注入等

## 建议执行顺序

1. 先完成 `P0`
2. 确认外部开发者能按文档跑通最小启动和 OIDC Discovery
3. 再补 `P1` 的 CI、部署、集成测试和文档分层
4. 最后再处理 `P2` 的协议增强和开源展示优化

## 发布完成的最低标准

满足以下条件后，再公开到 GitHub 会更稳妥：

- 有正式 `LICENSE`
- `yweb` 的安装方式明确
- 默认端口与文档一致
- `README.md`、`README_DEV.md`、`CONFIG_GUIDE.md` 口径一致
- 外部开发者能完成最小启动
- OIDC 接入方能通过 `oidc_issuer` 和 discovery 正常发现端点
- CI 至少能跑通关键测试
