# scripts

一次性运维 / 数据迁移脚本。**不是线上定时任务**，按需在目标环境执行。

连库的脚本都会读当前项目的 `config/settings.yaml`，因此拷到其他环境后，用该环境自己的配置直接跑即可。

```bash
# 建议先激活项目虚拟环境
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

python scripts/<脚本名>.py --help
```

写库脚本尽量先 `--dry-run` 看变更，确认无误再正式执行。

| 脚本 | 类型 | 用途 |
|---|---|---|
| `export_wechat_work_users.py` | 只读导出 | 从企微拉全员通讯录，落 JSON，并标出缺手机号 / 身份证号的人 |
| `backfill_employee_mobile_id_card.py` | 写库（可预览） | 用企微数据回填本地员工空着的手机号、身份证号 |
| `sync_username_to_wechat_userid.py` | 写库（可预览） | 把已关联员工的登录名改成企微 userid |
| `import_remote_org_users.py` | 写库 | 从远程 SSO 导出的 JSON 导入组织 / 部门 / 用户 |
| `import_sqlite_applications.py` | 写库 | 把旧 SQLite 里的应用表迁到当前数据库 |

`output/` 是导出产物目录，可重新生成，不要当源码维护。

---

## export_wechat_work_users.py

从企业微信通讯录接口按部门拉全员详情，去重后写成 JSON，并单独输出缺失清单。

**适用：** 对账、排查谁没填手机号 / 身份证号；不写业务库。

```bash
python scripts/export_wechat_work_users.py --corp-id wwxxxx --corp-secret '通讯录Secret'
# 或
set WECHAT_CORP_ID=wwxxxx
set WECHAT_CORP_SECRET=xxxx
python scripts/export_wechat_work_users.py
```

| 参数 | 说明 |
|---|---|
| `--corp-id` / `--corp-secret` | 企微凭证，也可用环境变量 `WECHAT_CORP_ID`、`WECHAT_CORP_SECRET` |
| `--out` | 全量导出路径，默认 `scripts/output/wechat_work_users.json` |
| `--missing-out` | 缺失清单路径，默认 `scripts/output/wechat_work_users_missing.json` |

产物含部门列表、去重后的成员、缺手机号 / 缺身份证号 / 两者都缺的统计。文件里有个人信息，不要提交到 Git。

---

## backfill_employee_mobile_id_card.py

对已绑定企业微信的组织，调用企微 `user/list`，给本地 `employee` **补空**：

- `mobile`：企微手机号，或从姓名等字段抠出的大陆手机号
- `id_card`：扩展属性「身份证号」

本地已有值不会覆盖。

**适用：** 同步通讯录后仍有员工缺手机号 / 身份证号。

```bash
python scripts/backfill_employee_mobile_id_card.py --dry-run
python scripts/backfill_employee_mobile_id_card.py
python scripts/backfill_employee_mobile_id_card.py --org-id 1
```

需要组织已绑定企微（`corp_id` + 通讯录 Secret）。

---

## sync_username_to_wechat_userid.py

把 `user.username` 改成关联员工的 `employee.enterprise_wechat_user_id`。

**适用：** 登录名仍是拼音 / 旧规则，要对齐企微 userid（下游知识库、乐享等也按这个键映射）。

只处理「已关联员工且员工有企微 userid」的账号。无员工、无 userid、userid 超过 50 字符、目标名被**不会改名**的人占用，会跳过并打印原因。互相占用时先改临时名再落到最终名。

```bash
python scripts/sync_username_to_wechat_userid.py --dry-run
python scripts/sync_username_to_wechat_userid.py
```

启动时会打印脱敏后的数据库 URL，请先确认连的是目标环境。改登录名后，用户需用新用户名登录，密码不变。

---

## import_remote_org_users.py

从远程 SSO 导出的两份 JSON 导入本地：

- 项目根目录 `users_list_response.json`：用户列表
- 项目根目录 `departments_tree.json`：部门树

会创建或更新组织（默认 id=1）、部门树、用户和角色。新用户写入默认密码（admin 与普通用户不同，见脚本内常量）。

**适用：** 一次性把旧 SSO 的人 / 部门迁到新库。会改用户、部门数据，不要在已有生产数据上随意重跑。

```bash
# 先把两份 JSON 放到项目根目录
python scripts/import_remote_org_users.py
```

脚本里有 PostgreSQL 序列重置（`setval`），当前库若是 MySQL 可能报序列相关警告，部门 / 用户写入仍可能成功，以日志为准。

---

## import_sqlite_applications.py

从旧 SQLite 文件 `app/db/y_sso.db` 读取 `application` 表，按 id 插入或更新到**当前** `settings.yaml` 指向的数据库。

**适用：** 从早期 SQLite 部署迁应用（client_id / secret / 回调地址等）。

```bash
python scripts/import_sqlite_applications.py
```

脚本末尾用 PostgreSQL 的 `setval` 校准自增 id，目标库是 MySQL 时这段可能失败；前面的插入 / 更新已完成的话，只需忽略或手工校准自增。

---

## 在其他环境执行

1. 使用该环境的代码和 `config/settings.yaml`（数据库指向该环境）。
2. 激活该环境的虚拟环境，保证能 `import app`、`import yweb`。
3. 写库脚本先 `--dry-run`（若支持），看输出的库地址和变更列表。
4. `export_wechat_work_users.py` 不连业务库，但需要该环境的企微通讯录 Secret。
